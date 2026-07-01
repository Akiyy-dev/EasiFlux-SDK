# EasiFlux SDK

EasiFlux SDK（`easiflux_sdk`）是为量化交易与桌面客户端准备的 Python SDK，封装 [EasiCoin](https://api.easicoin.io) 交易所 REST / WebSocket API。官方 API 文档：[https://www.easicoin.io/api-doc/zh-CN/common/Info](https://www.easicoin.io/api-doc/zh-CN/common/Info)。v0.2 起包名、主 Client 类名已统一为 **EasiFlux** 系列；旧名 `easicoin_sdk` 仅作兼容 shim。

## 命名规范

| 用途 | 名称 | 说明 |
|------|------|------|
| PyPI 安装包 | `EasiFlux-SDK` | `pip install EasiFlux-SDK` |
| Python import | `easiflux_sdk` | **推荐**，所有新代码应使用此包名 |
| 同步 Client | `EasiFluxSDK` | 主入口类 |
| 异步 Client | `AsyncEasiFluxSDK` | httpx 驱动 |
| 兼容 import（deprecated） | `easicoin_sdk` / `EasiCoinSDK` | v0.2–v0.3 可用，import 时触发 `DeprecationWarning`，v1.0 移除 |

```python
# 推荐写法
from easiflux_sdk import EasiFluxSDK, AsyncEasiFluxSDK

# 旧写法（仍可用，不推荐）
from easicoin_sdk import EasiCoinSDK  # = EasiFluxSDK
```

## 功能概览

当前版本默认配置对齐 EasiCoin 官方规则：

- 已实现统一请求入口和签名请求入口（Sync + Async）
- 已实现合约市场、订单、账户、持仓、资金账户和法币汇率接口
- 已实现异常体系、会话复用、重试和超时控制
- 已内置官方 Base URL、默认端点和认证请求头

### v0.3 新增

- **官方文档对齐**：REST 端点与 [EasiCoin Open API 文档](https://www.easicoin.io/api-doc/zh-CN/common/Info) 同步
- **新增公共行情**：`get_public_trades`、`get_funding_rate_history`、`get_mark_price_kline`、`get_instruments`、`get_risk_limit`、`get_market_close_time`
- **新增订单/仓位**：`cancel_all_orders`、`replace_order`、`get_trade_fills`、杠杆/保证金/止盈止损/合仓分仓等仓位接口
- **新增资金账户**：`get_user_id`、`get_transfer_history`
- **Async 对等**：`AsyncEasiFluxSDK` 现已覆盖全部同步 REST 方法
- **WebSocket 重写**：公共/私有双连接（`wss://ws.easicoin.io/contract/public/v1` / `private/v1`）、官方 topic 订阅、`15s` ping 心跳

### v0.2 新增

- **Sync + Async**：`EasiFluxSDK` / `AsyncEasiFluxSDK`（httpx）
- **数据模型**：`OrderRequest`、`OrderSide`、`OrderType` 等 dataclass
- **统一响应**：`SDKResponse[T]`（`response_typed=True` 时启用）
- **主动时间同步**：`sync_on_init=True` 启动时对时
- **WebSocket 框架**：订阅/重连/事件（`client.ws.subscribe(...)`）
- **事件系统**：`@client.on("order")` 装饰器（Async Client）
- **结构化日志**：`configure_logging(debug=True)`

## 官方规则摘要

- REST Base URL: `https://api.easicoin.io`
- WebSocket 合约公共: `wss://ws.easicoin.io/contract/public/v1`
- WebSocket 合约私有: `wss://ws.easicoin.io/contract/private/v1`
- 私有认证请求头: `Access-Key`, `Access-Sign`, `Access-Timestamp`, `Recv-Window`, `Content-Type: application/json`
- 签名串规则 GET: `Access-Timestamp + Access-Key + Recv-Window + queryString`
- 签名串规则 POST: `Access-Timestamp + Access-Key + Recv-Window + jsonBodyString`
- 签名算法: `HMAC-SHA256`
- 默认签名输出: 十六进制字符串
- 响应成功码: `code == 0`

说明：认证页表格里对 `Access-Sign` 的文字描述提到了 base64，但官方 Go/Python/Java 示例全部使用十六进制输出；SDK 默认跟随示例实现为十六进制，同时保留 `AuthConfig.signature_encoding` 可切换为 `base64`。

## 安装

```bash
pip install EasiFlux-SDK          # PyPI
pip install -e .                  # 本地开发
pip install -e ".[dev]"           # 含测试/ lint 工具
pip install -e ".[dev,websocket]" # 含 WebSocket 依赖
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

示例脚本 [examples/basic_usage.py](examples/basic_usage.py)（同步）和 [examples/async_usage.py](examples/async_usage.py)（异步）会自动读取项目根目录下的 `.env.dev`。

运行方式：

```bash
.venv/bin/python examples/basic_usage.py
.venv/bin/python examples/async_usage.py
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
            position_idx=1,
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
    position_idx=1,
    time_in_force=TimeInForce.GOOD_TILL_CANCEL,
)
sdk.create_order(order)  # 仍支持 dict 入参
```

## 设计说明

源码目录：`src/easiflux_sdk/`（`core/`、`models/`、`transport/`、`websocket/` 子包）。

### 1. 统一请求入口

- `_request` 负责 URL 组装、query 编码、JSON 序列化、超时、重试、HTTP 错误处理和响应解析
- `_signed_request` 按官方文档构造签名串，并将认证字段放入请求头
- 私有请求会自动和交易所服务器对时，并在检测到时间戳错误时强制同步后重试一次

### 2. 交易所特有规则集中配置

- `AuthConfig` 控制请求头名称、签名编码等少量兼容项
- `ResponseConfig` 控制错误码字段、成功码字段和错误消息字段
- `endpoint_map` 控制各业务方法对应的接口路径

### 3. 已内置的默认端点

完整列表见 [官方 API 文档](https://www.easicoin.io/api-doc/zh-CN/common/Info)。主要路径包括：

- 合约公共: `/futures/public/v1/market/*`、`/futures/public/v1/instruments`、`/futures/public/v1/position-risk-limit`
- 合约私有: 订单（`create-order`、`replace-order`、`cancel-all-orders`、`trade/fills` 等）、仓位（`set-leverage`、`create-tpsl` 等）、账户
- 资金: `get-funding-account-balance`、`user-account-transfer`、`userid`、`user-transfer-rercord/page`
- 法币汇率: `/asset-api/fiat/public/v1/rate`

## 当前支持的方法

同步与异步 Client 均支持以下方法：

- `get_server_time()`、`get_ticker()`、`get_kline()`、`get_depth()`
- `get_public_trades()`、`get_funding_rate_history()`、`get_mark_price_kline()`
- `get_instruments()`、`get_risk_limit()`、`get_market_close_time()`
- `get_trading_fee_rate()`、`get_balances()`、`get_positions()`
- `create_order()`、`cancel_order()`、`cancel_all_orders()`、`replace_order()`
- `get_order()` / `get_open_orders()`、`get_orders()`、`get_trade_fills()`
- `set_leverage()`、`add_margin()`、`close_all_positions()`、`get_closed_pnl()`
- `create_tpsl()`、`replace_tpsl()`、`switch_margin_mode()`、`switch_separate_position_mode()`
- `get_funding_balances()`、`transfer_between_accounts()`、`get_user_id()`、`get_transfer_history()`
- `get_fiat_rate()`

### WebSocket（Async Client）

```python
async with AsyncEasiFluxSDK(api_key="...", api_secret="...") as client:
    await client.ws.subscribe_ticker("BTCUSDT")
    await client.ws.subscribe_position()  # 私有频道，自动鉴权

    @client.on("order")
    async def on_order(event: dict) -> None:
        print(event)
```

旧版 `subscribe("ticker", {"symbol": "..."})` 仍可用但会触发 `DeprecationWarning`；推荐直接使用 `subscribe_ticker` / `subscribe_topic`。

## CI / Release

- CI 会在 push 和 pull request 上执行 `ruff check .`、`pytest -q` 和打包冒烟测试
- 发布流程由 `vX.X.X` tag 触发，要求 tag 版本和 `pyproject.toml` 中的版本完全一致
- Release workflow 会构建 wheel 和 sdist，并同时发布到 PyPI 与 GitHub Release
- 校验文件 `SHA256SUMS.txt` 只会附加到 GitHub Release，不会上传到 PyPI
- GitHub 官方当前支持的 GitHub Packages registry 列表不包含 Python registry，因此这里没有对 GitHub Packages 做 Python 包发布；发布成功后你会在 PyPI 页面和 GitHub Releases 页面看到产物，但不会在仓库的 Packages 页面看到 Python 包

## 未完成部分

- 现货 / 大宗交易 REST 尚未封装（官方文档当前仅提供 WS URL）
- 目前没有真实账户联调测试，建议先用只读接口和测试仓位做烟雾验证
