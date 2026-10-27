# Sơ đồ kiến trúc gateway-lab

```mermaid
flowchart TB
    C[Client / curl]
    G[Nginx API Gateway<br/>Host port 8080]
    A[Auth Service<br/>JWT issue / verify]
    GA[Gateway API<br/>Aggregation / Valet Key]
    U[User Service]
    O[Order Service]

    C --> G
    G -->|POST /auth/token| A
    G -->|auth_request /_auth| A
    G -->|/users and /users/*| U
    G -->|/orders and /orders/*| O
    G -->|/users/{id}/summary| GA
    G -->|/valet-keys/orders/{id}| GA
    G -->|/valet/orders/{id}| GA
    GA -->|GET user| U
    GA -->|GET orders by user_id| O
```

## Luồng request

1. Client lấy access token từ `POST /auth/token`.
2. Với API nghiệp vụ thông thường, Nginx dùng `auth_request` để yêu cầu Auth Service xác minh token rồi chuyển request đến service đích.
3. `GET /users/{id}/summary` gọi User Service và Order Service rồi tổng hợp dữ liệu.
4. `POST /valet-keys/orders/{id}` xác minh access token, kiểm tra order và phát hành Valet Key với scope `order:read`, resource `order:{id}`, TTL mặc định 300 giây.
5. `GET /valet/orders/{id}` tự xác minh Valet Key, scope và resource trước khi trả order.

Sơ đồ cần được đối chiếu với `gateway/nginx.conf`, `auth-service/app/main.py` và `gateway-api/app/main.py` của phiên bản cuối.
