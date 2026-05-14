# 🗳️ Hệ Thống Bầu Cử Ban Cán Sự

Web app bầu cử ban cán sự lớp, hỗ trợ 18 chức vụ, 2 học kỳ/năm, 2 vòng bầu cử.

## Cài đặt

```bash
# 1. Cài thư viện
pip install -r requirements.txt

# 2. Chạy app
python app.py
```

Mở trình duyệt vào: **http://localhost:5000**

## Tài khoản Admin

Đăng nhập bằng mã học sinh: `ADMIN`

> ⚠️ Nhớ thêm một học sinh với mã `ADMIN` trong trang quản lý học sinh, hoặc chạy lệnh SQL sau trong file `election.db`:
> ```sql
> INSERT INTO students (name, student_code) VALUES ('Admin', 'ADMIN');
> ```

## Hướng dẫn sử dụng

### Admin cần làm trước:
1. Đăng nhập bằng mã `ADMIN`
2. **Học sinh** → Thêm hoặc import danh sách lớp
3. **Học kỳ** → Thêm học kỳ và đặt làm "hiện tại"
4. **Quản lý bầu cử** → Mở bầu cử cho từng chức vụ

### Flow bầu cử:
1. Admin mở bầu cử → học sinh vào **Đề cử** (Vòng 1)
2. Admin chuyển sang Vòng 2 → học sinh vào **Bỏ phiếu** (Vòng 2)
3. Admin **Công bố kết quả** → người thắng được ghi vào lịch sử

## Quy tắc loại trừ

Một học sinh **không được bầu** cho chức vụ X nếu:
- Đang giữ bất kỳ chức vụ nào trong học kỳ hiện tại
- Đã từng giữ chức vụ X ở bất kỳ kỳ nào
- Đã giữ chức vụ nào đó ở học kỳ liền kề (HK1 ↔ HK2)

## Cấu trúc project

```
bau-cu-lop/
├── app.py           # Flask routes
├── database.py      # Database schema & init
├── helpers.py       # Logic lọc ứng viên, đếm phiếu
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── index.html
│   ├── nominate.html
│   ├── final_vote.html
│   ├── results.html
│   ├── history.html
│   ├── admin_students.html
│   ├── admin_terms.html
│   └── admin_elections.html
└── election.db      # Tự tạo khi chạy lần đầu
```
