# Báo cáo kiểm thử — gateway-lab

- Ngày kiểm thử: `YYYY-MM-DD`
- Môi trường: Windows + Docker Desktop + Docker Compose v2
- Commit/version: `GIT_COMMIT_OR_VERSION`
- Người kiểm thử: `NAME`

## 1. Bảng kết quả

Chỉ đánh dấu Pass sau khi chạy trên phiên bản code cuối và lưu bằng chứng.

| ID | Hạng mục | Kiểm thử | Kỳ vọng | Kết quả hiện có | Trạng thái cần báo cáo |
|---|---|---|---|---|---|
| T01 | Compose services | `docker compose config --services` | Hiển thị 5 service | Cần chạy lại bản cuối | Chưa xác nhận |
| T02 | Container health | `docker compose ps` | Các service `Up`/`healthy` | Cần chạy lại bản cuối | Chưa xác nhận |
| T03 | Nginx config | `docker compose exec gateway nginx -t` | syntax ok, test successful | Cần chạy lại bản cuối | Chưa xác nhận |
| T04 | User list | `GET /users` với access token | `200` | Đã kiểm thử trước đó thành công | Chạy lại trước khi nộp |
| T05 | User không tồn tại | `GET /users/999` | `404` | Đã kiểm thử trước đó thành công | Chạy lại trước khi nộp |
| T06 | Order list | `GET /orders` với access token | `200` | Đã kiểm thử trước đó thành công | Chạy lại trước khi nộp |
| T07 | Order không tồn tại | `GET /orders/999` | `404` | Đã kiểm thử trước đó thành công | Chạy lại trước khi nộp |
| T08 | JWT auth | Gọi `/users` không có token | `401` hoặc mã từ chối cấu hình | Chưa có kết quả được xác nhận ở log hiện có | Chưa xác nhận |
| T09 | Rate limiting | 50 request liên tiếp | Một số request trả `429` | Đã quan sát 29×`200`, 21×`429` ở một lần chạy | Chạy lại trước khi nộp |
| T10 | Aggregation | `GET /users/1/summary` | `200`, có user và orders | Chưa xác nhận được kết quả cuối | Chưa xác nhận |
| T11 | Cấp Valet Key | `POST /valet-keys/orders/2` | `200`, resource `order:2` | Đã nhận phản hồi `200` với resource `order:2` | Đã quan sát |
| T12 | Đọc đúng order | `GET /valet/orders/2` bằng Valet Key order 2 | `200` | Lần thử trước `401` do biến CMD gán sai | Cần chạy lại |
| T13 | Đọc order khác | `GET /valet/orders/1` bằng token order 2 | `403` | Chưa xác nhận với token được gán đúng | Chưa xác nhận |
| T14 | Valet token với API thường | `GET /users` bằng Valet Key | `401` | Chưa xác nhận | Chưa xác nhận |

## 2. Lệnh kiểm thử

### Kiểm tra cấu hình và service

```cmd
docker compose config --services
docker compose ps
docker compose exec gateway nginx -t
```

### JWT authentication

Lấy access token từ `POST /auth/token`, rồi gán trong CMD:

```cmd
set "TOKEN=PASTE_ACCESS_TOKEN_HERE"
```

Request không token:

```cmd
curl.exe -i "http://localhost:8080/users"
```

Request có token:

```cmd
curl.exe -i -H "Authorization: Bearer %TOKEN%" "http://localhost:8080/users"
```

### Rate limiting

```cmd
for /L %i in (1,1,50) do @curl.exe -s -o NUL -w "%{http_code}\n" -H "Authorization: Bearer %TOKEN%" "http://localhost:8080/users"
```

### Aggregation

```cmd
curl.exe -i -H "Authorization: Bearer %TOKEN%" "http://localhost:8080/users/1/summary"
```

### Valet Key

```cmd
curl.exe -s -X POST -H "Authorization: Bearer %TOKEN%" "http://localhost:8080/valet-keys/orders/2"
```

Sao chép toàn bộ `access_token` trong JSON:

```cmd
set "VALET_TOKEN=PASTE_WHOLE_VALET_TOKEN_HERE"
```

```cmd
curl.exe -i -H "Authorization: Bearer %VALET_TOKEN%" "http://localhost:8080/valet/orders/2"
curl.exe -i -H "Authorization: Bearer %VALET_TOKEN%" "http://localhost:8080/valet/orders/1"
curl.exe -i -H "Authorization: Bearer %VALET_TOKEN%" "http://localhost:8080/users"
```

## 3. Lưu bằng chứng

1. Tạo thư mục `evidence/` ở thư mục gốc.
2. Chụp ảnh terminal có lệnh và mã HTTP, không để lộ JWT/mật khẩu.
3. Đặt tên theo ID test, ví dụ `T10-aggregation.png`.
4. Với rate limiting, lưu output text và ghi số lượng từng mã HTTP.
5. Cập nhật bảng trên với kết quả thực tế và đường dẫn evidence.

## 4. Kết luận hiện tại

Định tuyến cơ bản đã hoạt động; rate limiting đã trả về `429` trong một thử nghiệm 50 request; endpoint cấp Valet Key đã trả về token với resource `order:2`. Tuy nhiên, cần chạy lại aggregation và ba phép thử giới hạn Valet Key với token được gán đúng trước khi kết luận toàn bộ test Phase 4 là Pass.
