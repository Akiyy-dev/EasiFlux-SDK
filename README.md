# EasiFlux SDK

这是一个为量化交易系统准备的 Python SDK 基础层，核心目标是干净、可靠、易维护，并把交易所特有的认证规则、响应格式和接口路径集中到可配置对象里。

当前版本已经根据你提供的 EasiCoin 官方文档落成了同步 REST SDK 基础层，默认配置直接对齐官方规则：

- 已实现统一请求入口和签名请求入口
- 已实现合约市场、订单、账户、持仓、资金账户和法币汇率接口
- 已实现异常体系、会话复用、重试和超时控制
- 已内置官方 Base URL、默认端点和认证请求头

## v0.2 新增能力

- **Sync + Async**：`EasiFluxSDK` / `AsyncEasiFluxSDK`（httpx）
- **数据模型**：`OrderRequest`、`OrderSide`、`OrderType` 等 dataclass
- **统一响应**：`SDKResponse[T]`（`response_typed=True` 时启用）
- **主动时间同步**：`sync_on_init=True` 启动时对时
- **WebSocket 框架**：订阅/重连/事件（`client.ws.subscribe(...)`）
- **事件系统**：`@client.on("order")` 装饰器（Async Client）
- **结构化日志**：`configure_logging(debug=True)`

## 包名说明（v0.2）

- **推荐 import**：`easiflux_sdk`，主 Client 类为 `EasiFluxSDK`
- **兼容 import**：`easicoin_sdk` / `EasiCoinSDK` 仍可用，但会触发 `DeprecationWarning`，将在 v1.0 移除

## 官方规则摘要

- REST Base URL: `https://api.easicoin.io`
- 私有认证请求头: `Access-Key`, `Access-Sign`, `Access-Timestamp`, `Recv-Window`, `Content-Type: application/json`
- 签名串规则 GET: `Access-Timestamp + Access-Key + Recv-Window + queryString`
- 签名串规则 POST: `Access-Timestamp + Access-Key + Recv-Window + jsonBodyString`
- 签名算法: `HMAC-SHA256`
- 默认签名输出: 十六进制字符串
- 响应成功码: `code == 0`

说明：认证页表格里对 `Access-Sign` 的文字描述提到了 base64，但官方 Go/Python/Java 示例全部使用十六进制输出；SDK 默认跟随示例实现为十六进制，同时保留 `AuthConfig.signature_encoding` 可切换为 `base64`。

## 安装

```bash
pip install -e .
pip install -e .[dev]
pip install -e ".[dev,websocket]"
```

## 测试前配置

项目根目录已经加入了 .env.dev 模板，你可以直接填入：

```env
EASICOIN_API_KEY=
EASICOIN_API_SECRET=
EASICOIN_BASE_URL=https://api.easicoin.io
EASICOIN_SYMBOL=BTCUSDT
EASICOIN_RECV_WINDOW=5000
```

示例脚本 [examples/basic_usage.py](examples/basic_usage.py) 会自动读取项目根目录下的 .env.dev。

运行方式：

```bash
g:/EasiFlux/EasiFlux-SDK/.venv/Scripts/python.exe examples/basic_usage.py
```

## 快速开始

```python
from easiflux_sdk import AuthConfig, EasiFluxSDK, ResponseConfig

sdk = EasiFluxSDK(
    api_key="your-api-key",
    api_secret="your-api-secret",
    auth_config=AuthConfig(
        signature_encoding="hex",
    ),
    response_config=ResponseConfig(
        code_fields=("code",),
        success_codes=(0, "0"),
        message_fields=("msg", "message"),
    ),
)

server_time = sdk.get_server_time()
ticker = sdk.get_ticker(symbol="BTCUSDT")
kline = sdk.get_kline(symbol="BTCUSDT", interval="1", limit=10)
depth = sdk.get_depth(symbol="BTCUSDT", depth=20)

balances = sdk.get_balances()
positions = sdk.get_positions(symbol="BTCUSDT")

order_result = sdk.create_order(
    {
        "symbol": "BTCUSDT",
        "position_idx": 1,
        "side": "Buy",
        "order_type": "Limit",
        "price": "60000",
        "qty": "0.001",
        "time_in_force": "GoodTillCancel",
        "order_link_id": "demo-order-001",
    }
)

open_orders = sdk.get_open_orders(symbol="BTCUSDT")
order_history = sdk.get_orders(symbol="BTCUSDT", limit=50)

funding_balances = sdk.get_funding_balances()
fiat_rate = sdk.get_fiat_rate(["EUR", "JPY"])
```

### 异步 Client

```python
import asyncio
from easiflux_sdk import AsyncEasiFluxSDK, OrderRequest, OrderSide, OrderType

async def main() -> None:
    async with AsyncEasiFluxSDK(api_key="...", api_secret="...") as client:
        ticker = await client.get_ticker(symbol="BTCUSDT")
        order = OrderRequest(
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            qty="0.001",
            price="50000",
        )
        result = await client.create_order(order)

asyncio.run(main())
```

完整示例见 [examples/async_usage.py](examples/async_usage.py)。

### 类型化下单

```python
from easiflux_sdk import EasiFluxSDK, OrderRequest, OrderSide, OrderType, TimeInForce

order = OrderRequest(
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    qty="0.001",
    price="60000",
    time_in_force=TimeInForce.GOOD_TILL_CANCEL,
)
sdk.create_order(order)  # 仍支持 dict 入参
```

## 设计说明

### 1. 统一请求入口

- `_request` 负责 URL 组装、query 编码、JSON 序列化、超时、重试、HTTP 错误处理和响应解析
- `_signed_request` 按官方文档构造签名串，并将认证字段放入请求头
- 私有请求会自动和交易所服务器对时，并在检测到时间戳错误时强制同步后重试一次

### 2. 交易所特有规则集中配置

- `AuthConfig` 控制请求头名称、签名编码等少量兼容项
- `ResponseConfig` 控制错误码字段、成功码字段和错误消息字段
- `endpoint_map` 控制各业务方法对应的接口路径

### 3. 已内置的默认端点

- 合约公共:
  - `/futures/public/v1/market/time`
  - `/futures/public/v1/market/tickers`
  - `/futures/public/v1/market/kline`
  - `/futures/public/v1/market/order-book`
- 合约私有:
  - `/futures/private/v1/account/fee-rate`
  - `/futures/private/v1/account/balance`
  - `/futures/private/v1/create-order`
  - `/futures/private/v1/cancel-order`
  - `/futures/private/v1/trade/activity-orders`
  - `/futures/private/v1/trade/orders`
  - `/futures/private/v1/position/list`
- 资金:
  - `/asset-api/account/private/v1/get-funding-account-balance`
  - `/asset-api/account/private/v1/user-account-transfer`
  - `/asset-api/fiat/public/v1/rate`

## 当前支持的方法

- `get_server_time()`
- `get_ticker()`
- `get_kline()`
- `get_depth()`
- `get_trading_fee_rate()`
- `get_balances()`
- `get_positions()`
- `create_order()`
- `cancel_order()`
- `get_order()` / `get_open_orders()`
- `get_orders()`
- `get_funding_balances()`
- `transfer_between_accounts()`
- `get_fiat_rate()`

## CI / Release

- CI 会在 push 和 pull request 上执行 `ruff check .`、`pytest -q` 和打包冒烟测试
- 发布流程由 `vX.X.X` tag 触发，要求 tag 版本和 `pyproject.toml` 中的版本完全一致
- Release workflow 会构建 wheel 和 sdist，并同时发布到 PyPI 与 GitHub Release
- 校验文件 `SHA256SUMS.txt` 只会附加到 GitHub Release，不会上传到 PyPI
- GitHub 官方当前支持的 GitHub Packages registry 列表不包含 Python registry，因此这里没有对 GitHub Packages 做 Python 包发布；发布成功后你会在 PyPI 页面和 GitHub Releases 页面看到产物，但不会在仓库的 Packages 页面看到 Python 包

## 未完成部分

- WebSocket 频道报文格式需与官方文档进一步对齐（当前为可配置 adapter 框架）
- 合约分类里还有部分高级仓位接口和订单扩展接口未封装
- 目前没有真实账户联调测试，建议先用只读接口和测试仓位做烟雾验证
