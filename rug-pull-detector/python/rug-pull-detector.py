from web3 import Web3
import datetime
import io
import sys
from decimal import Decimal

from eth_utils import event_signature_to_log_topic   # NEW – pip install eth-utils if needed


uniswap_v2_factory_abi = [  # Minimal ABI for Factory contract
    {
        "constant": True,
        "inputs": [{"name": "tokenA", "type": "address"}, {"name": "tokenB", "type": "address"}],
        "name": "getPair",
        "outputs": [{"name": "", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "allPairsLength",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "uint", "type": "uint256"}],
        "name": "allPairs",
        "outputs": [{"name": "pair", "type": "address"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

pair_abi = [
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}],
     "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}],
     "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "getReserves",
     "outputs": [{"name": "reserve0", "type": "uint112"}, {"name": "reserve1", "type": "uint112"},
                 {"name": "blockTimestampLast", "type": "uint32"}], "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}],
     "stateMutability": "view", "type": "function"}
]

token_abi = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}],
     "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}],
     "stateMutability": "view", "type": "function"},
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}],
     "stateMutability": "view", "type": "function"}
]

BASE_RPC_URL = "https://base.drpc.org"  # Base RPC URL
web3 = Web3(Web3.HTTPProvider(BASE_RPC_URL))

# Ensure the connection to the Base chain
if web3.is_connected():
    print("Connected to Base Chain")

# Input token address 
input_token_address = "0x768BE13e1680b5ebE0024C42c896E3dB59ec0149"

# Uniswap V2 Factory contract address 
uniswap_v2_factory_address = "0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6"

# Do not change these. Will be used to find the pair with USDC or WETH
USDC_contract = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
WETH_contract = '0x4200000000000000000000000000000000000006'
ZERO_address = '0x0000000000000000000000000000000000000000'

# Create contract instance for the Uniswap V2 Factory
factory_contract = web3.eth.contract(address=web3.to_checksum_address(uniswap_v2_factory_address),
                                     abi=uniswap_v2_factory_abi)

def get_token_decimals(token_address):
    if token_address == USDC_contract:
        return 6
    if token_address == WETH_contract:
        return 18
    
    token_contract = web3.eth.contract(address=web3.to_checksum_address(token_address), abi=token_abi)
    return token_contract.functions.decimals().call()

def get_token_total_supply(token_address):
    token_contract = web3.eth.contract(address=web3.to_checksum_address(token_address), abi=token_abi)
    return token_contract.functions.totalSupply().call()

def check_minting_ability(token_contract):
    try:
        token_contract.functions.mint().call()
        return {"mintable": True, "supplyStatus": "NOT FIXED"}
    except:
        return {"mintable": False, "supplyStatus": "FIXED"}

def find_pair_by_token(token_address):
    pair_address_usdc = factory_contract.functions.getPair(
        web3.to_checksum_address(token_address),
        web3.to_checksum_address(USDC_contract)
    ).call()
    
    if pair_address_usdc != ZERO_address:
        return {"pairAddress": pair_address_usdc, "quoteToken": "USDC"}
    
    pair_address_weth = factory_contract.functions.getPair(
        web3.to_checksum_address(token_address),
        web3.to_checksum_address(WETH_contract)
    ).call()
    
    if pair_address_weth != ZERO_address:
        return {"pairAddress": pair_address_weth, "quoteToken": "WETH"}
    
    return None

def calculate_market_cap(pair_contract):
    try:
        reserves = pair_contract.functions.getReserves().call()
        token0 = pair_contract.functions.token0().call()
        token1 = pair_contract.functions.token1().call()
        
        token_total_supply = get_token_total_supply(token0)
        
        # Normalize values using decimals
        reserve0_normalized = Decimal(reserves[0]) / Decimal(10 ** get_token_decimals(token0))
        reserve1_normalized = Decimal(reserves[1]) / Decimal(10 ** get_token_decimals(token1))
        price_per_token = reserve1_normalized / reserve0_normalized
        total_supply_normalized = Decimal(token_total_supply) / Decimal(10 ** get_token_decimals(token0))
        market_cap = total_supply_normalized * price_per_token
        
        return {
            "reserves": reserves,
            "token0": token0,
            "token1": token1,
            "pricePerToken": str(price_per_token),
            "totalSupplyNormalized": str(total_supply_normalized),
            "marketCap": str(market_cap)
        }
    except Exception as e:
        print(f"Error calculating market cap: {e}")
        return None
# ---------- SIMPLE RUG-PULL CHECK ---------- #
def get_liquidity_ratio(pair_contract, token_address):
    """
    Returns the percentage of the token's total supply that is locked as
    liquidity in this Uniswap-V2-style pair.
    """
    reserves = pair_contract.functions.getReserves().call()
    token0 = pair_contract.functions.token0().call()
    token_decimals = get_token_decimals(token_address)

    # Figure out which reserve belongs to the token we're analysing
    token_reserve_raw = reserves[0] if token_address.lower() == token0.lower() else reserves[1]
    token_reserve = Decimal(token_reserve_raw) / Decimal(10 ** token_decimals)

    total_supply_raw = get_token_total_supply(token_address)
    total_supply = Decimal(total_supply_raw) / Decimal(10 ** token_decimals)

    # Avoid division-by-zero on weird tokens
    ratio = (token_reserve / total_supply) if total_supply > 0 else Decimal(0)
    return ratio  # 0-1 scale

def rugpull_check(token_contract, pair_contract, token_address,
                  min_liquidity_pct=Decimal('0.05')):
    """
    Very naive rug-pull heuristic:
      • FAIL if liquidity ratio ≤ min_liquidity_pct
      • FAIL if token is mintable
    Returns dict with details + overall verdict.
    """
    liquidity_ratio = get_liquidity_ratio(pair_contract, token_address)
    mint_info = check_minting_ability(token_contract)

    fail_reasons = []
    if liquidity_ratio <= min_liquidity_pct:
        fail_reasons.append(f"Liquidity ratio only {liquidity_ratio*100:.2f}% (≤ {min_liquidity_pct*100}%)")
    if mint_info["mintable"]:
        fail_reasons.append("Token contract can still mint new supply")

    return {
        "liquidityRatio": liquidity_ratio,
        "mintable": mint_info["mintable"],
        "verdict": "FAIL" if fail_reasons else "PASS",
        "reasons": fail_reasons
    }
# ---------- END RUG-PULL CHECK ---------- #


# If High volume with low number of holders, rug
# If low volume with high number of holders, safe


# Main execution
pair_info = find_pair_by_token(input_token_address)
if pair_info is None:
    print("Pair could not be found! Quit execution of the algorithm...")
    quit()

pair_address = pair_info["pairAddress"]
pair_contract = web3.eth.contract(address=web3.to_checksum_address(pair_address), abi=pair_abi)

# Get token addresses
token0 = pair_contract.functions.token0().call()
token1 = pair_contract.functions.token1().call()
input_token = token0 if token0 != USDC_contract and token0 != WETH_contract else token1
pair_token = token0 if token0 == USDC_contract or token0 == WETH_contract else token1

# Create contract instances
token_contract = web3.eth.contract(address=input_token, abi=token_abi)
pair_token_contract = web3.eth.contract(address=pair_token, abi=token_abi)

buffer = io.StringIO()
sys.stdout = buffer

print("=" * 80)
print("🔍 TOKEN ANALYSIS REPORT")
print("=" * 80)
print(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("-" * 80)

# Token Information
print("\n📊 TOKEN INFORMATION")
print("-" * 40)
print(f"Token Address: {input_token}")
token_name = token_contract.functions.name().call()
token_symbol = token_contract.functions.symbol().call()
print(f"Token Name: {token_name}")
print(f"Token Symbol: {token_symbol}")

# Pair Token Information
print("\n🔄 PAIR TOKEN INFORMATION")
print("-" * 40)
print(f"Pair Token Address: {pair_token}")
pair_token_name = pair_token_contract.functions.name().call()
pair_token_symbol = pair_token_contract.functions.symbol().call()
print(f"Pair Token Name: {pair_token_name}")
print(f"Pair Token Symbol: {pair_token_symbol}")

# Liquidity Information
print("\n💧 LIQUIDITY INFORMATION")
print("-" * 40)
print(f"Liquidity Pair Address: {pair_address}")
total_lp_tokens = pair_contract.functions.totalSupply().call()
print(f"Total Supply of LP Tokens: {total_lp_tokens}")

# Market Analysis
print("\n💰 MARKET ANALYSIS")
print("-" * 40)
market_cap_data = calculate_market_cap(pair_contract)
if market_cap_data:
    print(f"Reserve {token_symbol}: {market_cap_data['reserves'][0]}")
    print(f"Reserve {pair_token_symbol}: {market_cap_data['reserves'][1]}")
    print(f"Price per {token_symbol}: {market_cap_data['pricePerToken']} {pair_token_symbol}")
    print(f"Total Supply: {market_cap_data['totalSupplyNormalized']}")
    print(f"Market Cap: {market_cap_data['marketCap']} {pair_token_symbol}")

# Supply Analysis
print("\n🪄 SUPPLY ANALYSIS")
print("-" * 40)
minting_status = check_minting_ability(token_contract)
print(f"Mint Status: {'MINTABLE' if minting_status['mintable'] else 'NOT MINTABLE'}")
print(f"Total Supply Status: {minting_status['supplyStatus']}")


# Rug-pull Heuristic
print("\n🚨 RUG-PULL HEURISTIC")
print("-" * 40)
rug = rugpull_check(token_contract, pair_contract, input_token)
print(f"Liquidity / Supply Ratio: {rug['liquidityRatio']*100:.2f}%")
print(f"Mintable: {'YES' if rug['mintable'] else 'NO'}")

if rug["verdict"] == "PASS":
    print("✅ Verdict: PASS – no blatant red flags")
else:
    print("❌ Verdict: FAIL – potential risks detected")
    for r in rug["reasons"]:
        print(f"  • {r}")




print("\n" + "=" * 80)
print("End of Report")
print("=" * 80)

sys.stdout = sys.__stdout__

output_text = buffer.getvalue()

# Save to text file
txt_filename = '/Users/jonas/Ocean-Node-workshop/results/result-output_2025-05-16T18-40-01-188Z_extracted/outputs/report.txt'
with open(txt_filename, 'w') as f:
    f.write(output_text)

print(f"✅ Output saved to {txt_filename} \n")
print(output_text)
