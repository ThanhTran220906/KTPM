# gateway-lab — API Gateway với Docker Compose

> Bài tập Kiến trúc phần mềm: API Gateway cho User và Order Service, JWT Authentication, Rate Limiting, Aggregation API và Valet Key.

## 1. Mục tiêu

- Định tuyến request đến User Service và Order Service.
- Xác thực request bằng JWT thông qua Auth Service và Nginx `auth_request`.
- Giới hạn tốc độ request theo IP bằng Nginx Rate Limiting.
- Tổng hợp dữ liệu user và orders qua Gateway API.
- Cấp Valet Key có thời hạn và giới hạn theo tài nguyên để đọc một đơn hàng.

## 2. Sơ đồ kiến trúc

```mermaid
    Client -->|HTTP| Gateway
    Gateway -->|POST /auth/token| Auth
    Gateway -->|auth_request /_auth| Auth
    Gateway -->|/users and /users/*| User
    Gateway -->|/orders and /orders/*| Order
    Gateway -->|/users/{id}/summary| API
    Gateway -->|/valet-keys/orders/{id}| API
    Gateway -->|/valet/orders/{id}| API
    API -->|GET user| User
    API -->|GET orders by user_id| Order
```

## 3. Thành phần

| Thành phần | Vai trò | Cổng |
|---|---|---|
| `gateway` | Nginx reverse proxy, routing, `auth_request`, rate limiting | Host `8080` |
| `auth-service` | Cấp và xác minh JWT access token | Nội bộ Docker network |
| `gateway-api` | Aggregation API, cấp/kiểm tra Valet Key | Nội bộ Docker network |
| `user-service` | API user | Host `8001`, container `8000` |
| `order-service` | API order | Host `8002`, container `8000` |
| `backend` | Docker bridge network | Nội bộ |

> Các cổng `8001` và `8002` được publish theo cấu hình hiện tại để thuận tiện phát triển. Khi triển khai thực tế, nên cân nhắc chỉ expose Gateway.

## 4. Cấu trúc thư mục dự kiến

Đối chiếu với repository thực tế trước khi nộp.

```text
gateway-lab/
├── docker-compose.yml
├── .env.example
├── README.md
├── gateway/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── nginx.benchmark.conf
├── auth-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/main.py
├── gateway-api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/main.py
├── user-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
└── order-service/
    ├── Dockerfile
    ├── requirements.txt
    └── app/
```

## 5. Yêu cầu và cấu hình

- Docker Desktop đang chạy.
- Docker Compose v2 (`docker compose`).
- Windows CMD hoặc terminal tương đương.

Sử dụng `.env` để cấu hình secrets; không commit `.env`, mật khẩu thật hoặc JWT vào Git. Thay secret mặc định bằng chuỗi ngẫu nhiên đủ dài trước khi chạy trong môi trường dùng chung.

Ví dụ `.env.example`:

```dotenv
JWT_SECRET=replace-with-a-long-random-secret
DEMO_USERNAME=demo
DEMO_PASSWORD=change-this-demo-password
```

## 6. Chạy dự án

Từ thư mục gốc `gateway-lab`:

```cmd
docker compose config --services
docker compose up -d --build
docker compose ps
docker compose exec gateway nginx -t
curl.exe -i http://localhost:8080/health
```

Danh sách service dự kiến: `user-service`, `order-service`, `auth-service`, `gateway-api`, `gateway`.

Dừng hệ thống:

```cmd
docker compose down
```

Xem log:

```cmd
docker compose logs --tail=100 gateway
docker compose logs --tail=100 auth-service
docker compose logs --tail=100 gateway-api
docker compose logs --tail=100 user-service
docker compose logs --tail=100 order-service
```

## 7. API chính

| Method | Endpoint | Mô tả | Xác thực |
|---|---|---|---|
| `GET` | `/health` | Health check Gateway | Không |
| `POST` | `/auth/token` | Lấy access token demo | Thông tin đăng nhập demo |
| `GET` | `/users` | Danh sách user | Access token |
| `GET` | `/users/{user_id}` | Chi tiết user | Access token |
| `POST` | `/users` | Tạo user | Access token |
| `GET` | `/orders` | Danh sách order, có thể lọc `user_id` | Access token |
| `GET` | `/orders/{order_id}` | Chi tiết order | Access token |
| `POST` | `/orders` | Tạo order | Access token |
| `GET` | `/users/{user_id}/summary` | Tổng hợp user và orders | Access token |
| `POST` | `/valet-keys/orders/{order_id}` | Cấp Valet Key | Access token |
| `GET` | `/valet/orders/{order_id}` | Đọc order bằng Valet Key | Valet Key phù hợp |

Đối chiếu bảng endpoint với source code cuối trước khi nộp.

## 8. Kiểm thử thủ công trên Windows CMD

### 8.1 Lấy access token

Tạo `login.json` nếu chưa có:

```cmd
echo {"username":"demo","password":"demo123"} > login.json
```

Lấy token:

```cmd
curl.exe -s -X POST "http://localhost:8080/auth/token" -H "Content-Type: application/json" --data-binary "@login.json"
```

Sao chép `access_token` trong JSON rồi gán:

```cmd
set "TOKEN=PASTE_ACCESS_TOKEN_HERE"
```

Không gửi token lên báo cáo hoặc Git.

### 8.2 API nghiệp vụ

```cmd
curl.exe -i -H "Authorization: Bearer %TOKEN%" "http://localhost:8080/users"
curl.exe -i -H "Authorization: Bearer %TOKEN%" "http://localhost:8080/users/1"
curl.exe -i -H "Authorization: Bearer %TOKEN%" "http://localhost:8080/orders"
curl.exe -i -H "Authorization: Bearer %TOKEN%" "http://localhost:8080/orders?user_id=1"
```

### 8.3 Aggregation API

```cmd
curl.exe -i -H "Authorization: Bearer %TOKEN%" "http://localhost:8080/users/1/summary"
```

Kỳ vọng `200 OK`, gồm user, orders và tổng số order.

### 8.4 Valet Key

Cấp Valet Key cho order số 2:

```cmd
curl.exe -s -X POST -H "Authorization: Bearer %TOKEN%" "http://localhost:8080/valet-keys/orders/2"
```

Sao chép toàn bộ `access_token` trong phản hồi rồi gán:

```cmd
set "VALET_TOKEN=PASTE_WHOLE_VALET_TOKEN_HERE"
```

Đọc đúng order:

```cmd
curl.exe -i -H "Authorization: Bearer %VALET_TOKEN%" "http://localhost:8080/valet/orders/2"
```

Đọc order khác:

```cmd
curl.exe -i -H "Authorization: Bearer %VALET_TOKEN%" "http://localhost:8080/valet/orders/1"
```

Dùng Valet Key cho API thông thường:

```cmd
curl.exe -i -H "Authorization: Bearer %VALET_TOKEN%" "http://localhost:8080/users"
```

Kết quả dự kiến lần lượt: `200`, `403`, `401`. Valet Key có TTL mặc định 300 giây.

### 8.5 Rate limiting

```cmd
for /L %i in (1,1,50) do @curl.exe -s -o NUL -w "%{http_code}\n" -H "Authorization: Bearer %TOKEN%" "http://localhost:8080/users"
```

Một lần kiểm thử trước đó ghi nhận 29 phản hồi `200` và 21 phản hồi `429`. Kết quả có thể thay đổi theo thời điểm và cấu hình.
