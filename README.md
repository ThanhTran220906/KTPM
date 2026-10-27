
# Gateway Lab

Bài lab kiến trúc phần mềm: API Gateway, Routing và microservices.

## 1. Yêu cầu môi trường

- Docker Engine hoặc Docker Desktop.
- Docker Compose v2.
- Các cổng 8080, 8001, 8002 chưa bị ứng dụng khác chiếm dụng.

Không cần cài Python trên máy host.

## 2. Khởi chạy

Chạy tại thư mục gateway-lab:

```bash
docker compose up --build -d
```

Kiểm tra trạng thái:

```bash
docker compose ps
docker compose logs -f gateway user-service order-service
```

Dừng hệ thống:

```bash
docker compose down
```

## 3. Kiểm tra healthcheck

```bash
curl -i http://localhost:8080/health
curl -i http://localhost:8001/health
curl -i http://localhost:8002/health
```

Kết quả mong đợi: HTTP 200 và JSON có trường `status: ok`.

## 4. Routing: User Service

Lấy danh sách user qua gateway:

```bash
curl -i http://localhost:8080/users
```

Lấy user ID 1 qua gateway:

```bash
curl -i http://localhost:8080/users/1
```

Gọi trực tiếp User Service:

```bash
curl -i http://localhost:8001/users
curl -i http://localhost:8001/users/1
```

Tạo user mới:

```bash
curl -i -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name":"David Pham","email":"david@example.com","role":"user"}'
```

## 5. Routing: Order Service

Lấy toàn bộ đơn hàng:

```bash
curl -i http://localhost:8080/orders
```

Lấy đơn hàng ID 1:

```bash
curl -i http://localhost:8080/orders/1
```

Lọc đơn hàng của user ID 1:

```bash
curl -i "http://localhost:8080/orders?user_id=1"
```

Gọi trực tiếp Order Service:

```bash
curl -i http://localhost:8002/orders
curl -i "http://localhost:8002/orders?user_id=1"
```

Tạo đơn hàng:

```bash
curl -i -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"item":"USB Cable","quantity":2,"amount":9.99,"status":"pending"}'
```

## 6. Kiểm tra lỗi định tuyến

```bash
curl -i http://localhost:8080/unknown
curl -i http://localhost:8080/users/999
curl -i http://localhost:8080/orders/999
```

Các request không có route phù hợp sẽ nhận HTTP 404. User hoặc order không tồn tại cũng nhận HTTP 404 từ service tương ứng.

## 7. Kiểm tra Nginx access log

```bash
docker compose logs gateway
```

Hoặc đọc log trực tiếp trong container:

```bash
docker compose exec gateway \
  cat /var/log/nginx/access.log
```

Các trường cần chú ý:

- `request_time`: tổng thời gian Nginx xử lý request.
- `upstream_response_time`: thời gian chờ upstream phản hồi.
- `upstream_addr`: địa chỉ upstream được chọn.
- `status`: mã HTTP trả về client.

## 8. Các giới hạn của Giai đoạn 1

- Chưa có JWT hoặc endpoint đăng nhập.
- Chưa có rate limiting.
- Chưa có Aggregation `/dashboard`.
- Chưa có MinIO hoặc upload avatar.
- Dữ liệu user/order được lưu trong RAM và không bền vững sau khi container khởi động lại.

Các chức năng này sẽ được bổ sung ở các giai đoạn tiếp theo.
