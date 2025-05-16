# 🧪 Uniswap V2 Liquidity Pool Analyzer

This tool is designed to analyze the token pairs characteristics using **Uniswap V2** smart contracts
on **Base chain**.

It inspects various characteristics of the tokens involved in each pair and prints key risk and health
indicators. The results are saved into a text report (`report.txt`) titled "TOKEN ANALYSIS REPORT".

## 🔍 What the Script Does

1. Connects to the Base chain via an RPC endpoint.
2. Interacts with the Uniswap V2 Factory contract.
3. Based on the input token address, it finds the corresponding pair backed up by WETH or USDC.
4. For each pair, it fetches:

   - Pair address
   - Token details (name, symbol, addresses)
   - Total Supply of LP Tokens
   - Market cap (calculated based on liquidity pool reserves)
   - Minting capabilities
   - Total Supply Status

5. Prints results to console and saves them to a text file.

## 📊 Parameters Analyzed Per Token or Pair

| Parameter                   | Description                                                |
| --------------------------- | :--------------------------------------------------------: |
| `Token Name / Symbol`       | Identity of the token in the pair                         |
| `Total Supply of LP Tokens` | How many LP tokens exist for the pair                     |
| `Market Cap`                | Estimated based on liquidity pool reserves                |
| `Minting Ability`           | Can new tokens be minted? `MINTABLE` or `NOT MINTABLE`    |
| `Total Supply Status`       | If minting is disabled, it's `FIXED`; otherwise `NOT FIXED` |

## 📁 Input

- Input token address
- Uniswap V2 Factory contract address **(no need to update this if using uniswap v2 on Base)**
- Base chain RPC endpoint **(no need to update for running on base)**

**Note:**
- You can use [The graph](https://thegraph.com/explorer/subgraphs/D31gzGUtVNhHNdnxeELUBdch5rzDRm5cddvae9GzhCLu?view=Query) to fetch new token addresses
```
{
  tokens(first: 5, orderBy: tradeVolumeUSD, orderDirection: desc) {
    id
    symbol
    name
    decimals
  }
}
``` 




## 📁 Output
- Console output with all parameters per pair
- A text report saved as `report.txt` in the `data/outputs` directory
- Title: `"TOKEN ANALYSIS REPORT"`

## How to run your algorithm on Ocean Node

```bash
1. Open Ocean Protocol vscode-extension
2. Select Algorithm file
3. Select Results folder
4. Press Start Compute Job
```

#  Python
### Use existing docker image `oceanprotocol/c2d_examples:py-general`:

- Docker image: `oceanprotocol/c2d_examples`
- Docker tag: `py-general`

#  Node.js
### Use existing docker image `oceanprotocol/c2d_examples:js-general`:
- Docker image: `oceanprotocol/c2d_examples`
- Docker tag: `js-general`

## 🔐 Disclaimer
This tool is for research and educational purposes. It is not a financial advice tool.




Changes made:
If theres theres high volume with a low number of wallets then this is a rug
if theres a low level of volume with low lwallet count or high volume with high wallet count then this is safe

Liquidity-Ratio / Mintability check – flags tokens whose liquidity pool holds ≤ 5 % of total supply or whose contract can still mint new tokens