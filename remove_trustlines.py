import asyncio
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.models.requests import AccountLines, AccountInfo
from xrpl.models.transactions import TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.wallet import Wallet
from xrpl.asyncio.transaction import submit_and_wait, autofill_and_sign
import sys
import os
from getpass import getpass


class TrustLineRemover:
    def __init__(self, seed, websocket_url="wss://xrpl.ws/"):
        self.wallet = Wallet.from_seed(seed)
        self.client = AsyncWebsocketClient(websocket_url)
        self.initial_owner_count = 0
        
    async def connect(self):
        await self.client.open()
        
    async def close(self):
        await self.client.close()
        
    async def get_account_info(self):
        response = await self.client.request(AccountInfo(account=self.wallet.address))
        if response.is_successful():
            data = response.result['account_data']
            return {
                'owner_count': data.get('OwnerCount', 0),
                'balance': int(data['Balance']) / 1_000_000
            }
        return None
        
    async def get_zero_balance_trustlines(self):
        zero_balance_lines = []
        marker = None
        
        while True:
            try:
                response = await asyncio.wait_for(
                    self.client.request(AccountLines(
                        account=self.wallet.address,
                        limit=400,
                        marker=marker
                    )),
                    timeout=30
                )
                
                if response.is_successful():
                    lines = response.result.get('lines', [])
                    
                    for line in lines:
                        balance = float(line.get('balance', 0))
                        if balance == 0:
                            zero_balance_lines.append(line)
                    
                    marker = response.result.get('marker')
                    if not marker:
                        break
                else:
                    break
                    
            except asyncio.TimeoutError:
                print("Timeout while fetching trust lines, retrying...")
                await asyncio.sleep(2)
                continue
                
        return zero_balance_lines
        
    async def remove_trustline(self, currency, issuer):
        trust_set = TrustSet(
            account=self.wallet.address,
            limit_amount=IssuedCurrencyAmount(
                currency=currency,
                issuer=issuer,
                value="0"
            ),
            flags=2228224,  # tfSetNoRipple + tfClearFreeze
            quality_in=0,
            quality_out=0
        )
        
        signed = await autofill_and_sign(trust_set, self.client, self.wallet)
        result = await submit_and_wait(signed, self.client)
        
        return result.is_successful(), result.result.get('engine_result', 'Unknown')
        
    async def run(self):
        await self.connect()
        
        try:
            print(f"Wallet address: {self.wallet.address}")
            print("-" * 50)
            
            account_info = await self.get_account_info()
            if not account_info:
                print("Failed to get account information")
                return
                
            self.initial_owner_count = account_info['owner_count']
            print(f"Initial OwnerCount: {self.initial_owner_count}")
            print(f"Balance: {account_info['balance']} XRP")
            
            print("\nFetching trust lines...")
            trustlines = await self.get_zero_balance_trustlines()
            print(f"Found {len(trustlines)} trust lines with zero balance")
            
            if not trustlines:
                print("No trust lines to remove")
                return
                
            print(f"\nRemoving {len(trustlines)} trust lines...")
            print("-" * 50)
            
            success_count = 0
            redundant_count = 0
            failed_count = 0
            
            for i, line in enumerate(trustlines):
                currency = line.get('currency')
                issuer = line.get('account')
                
                if i % 10 == 0:
                    percent = ((i + 1) / len(trustlines)) * 100
                    print(f"\nProgress: {percent:.1f}% ({i+1}/{len(trustlines)})")
                    
                    current_info = await self.get_account_info()
                    if current_info:
                        print(f"Current OwnerCount: {current_info['owner_count']}")
                
                success, error = await self.remove_trustline(currency, issuer)
                
                if success:
                    success_count += 1
                elif error == 'tecNO_LINE_REDUNDANT':
                    redundant_count += 1
                else:
                    failed_count += 1
                    print(f"Failed to remove {currency[:8]}...{issuer[:8]}: {error}")
                
                await asyncio.sleep(0.1)
            
            print("\n" + "=" * 50)
            print("RESULTS:")
            print(f"Successfully removed: {success_count}")
            print(f"Already removed: {redundant_count}")
            print(f"Failed: {failed_count}")
            
            final_info = await self.get_account_info()
            if final_info:
                print(f"\nOwnerCount: {self.initial_owner_count} -> {final_info['owner_count']}")
                print(f"Released reserve: {(self.initial_owner_count - final_info['owner_count']) * 0.2} XRP")
                
                if final_info['owner_count'] == 0:
                    print("\nAccount is ready for deletion!")
                    
        finally:
            await self.close()


async def main():
    print("XRPL Trust Line Removal Tool")
    print("=" * 50)
    print("This tool removes trust lines with zero balance from your XRPL account.")
    print("Each trust line reserves 0.2 XRP. Removing them releases the reserve.")
    print()
    
    seed = os.environ.get('XRPL_SEED')
    if not seed:
        seed = getpass("Enter your XRPL account seed (starts with 's'): ")
    
    if not seed.startswith('s'):
        print("Error: Invalid seed format. Seed must start with 's'")
        sys.exit(1)
    
    print(f"\nWARNING: This will remove ALL trust lines with zero balance.")
    confirm = input("Type 'REMOVE ALL' to confirm: ")
    
    if confirm != "REMOVE ALL":
        print("Operation cancelled")
        sys.exit(0)
    
    remover = TrustLineRemover(seed)
    await remover.run()


if __name__ == "__main__":
    asyncio.run(main())