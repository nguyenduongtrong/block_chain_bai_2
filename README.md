# 🔐 Multi-Algo Blockchain Wallet (Ví Blockchain Đa Thuật Toán)

## 📖 Giới thiệu

Đây là ứng dụng ví tiền điện tử dòng lệnh (CLI) mô phỏng hoạt động của
các ví Non-custodial hiện đại (như Metamask, Phantom). Điểm đặc biệt của
dự án là khả năng hỗ trợ đa thuật toán chữ ký (Multi-Algorithm Signing),
cho phép tạo và quản lý ví trên nhiều nền tảng Blockchain khác nhau từ
cùng một hạt giống (Seed Phrase).

## 🚀 Tính năng nổi bật

### Hỗ trợ đa thuật toán (Multi-Chain Support):

-   ECDSA (secp256k1): Chuẩn của Ethereum, Bitcoin (Legacy).
-   Ed25519: Chuẩn hiện đại, tốc độ cao của Solana, Aptos, Sui.
-   Schnorr (BIP-340): Chuẩn chữ ký mới của Bitcoin (Taproot), hỗ trợ
    gộp chữ ký và quyền riêng tư cao.

### Khôi phục ví chuẩn BIP-39:

-   Sử dụng 12 từ khóa bí mật (Mnemonic Seed Phrase) dễ nhớ để sao lưu
    và khôi phục ví.
-   Tính chất Tất định (Deterministic): Mất thiết bị không mất tiền, chỉ
    cần nhớ 12 từ khóa.

### Lưu trữ an toàn (Persistence):

-   Tự động lưu trạng thái ví (đã mã hóa cơ bản) vào file keystore.json.
-   Không cần nhập lại khóa mỗi khi thực hiện giao dịch.

### Đánh giá hiệu năng (Benchmarking):

-   Công cụ tích hợp sẵn để đo lường và so sánh tốc độ tạo khóa/ký giữa
    các thuật toán (phục vụ mục đích nghiên cứu).

## 🛠 Cài đặt

### Yêu cầu: Python 3.7 trở lên.

### Cài đặt thư viện:

    pip install -r requirements.txt

(File requirements.txt bao gồm: click, tabulate, eth-keys, eth-utils,
pynacl, coincurve, mnemonic)

## 🎮 Hướng dẫn sử dụng (Command Line)

Cú pháp chung: `python main.py [COMMAND] [OPTIONS]`

| Lệnh      | Mô tả                             | Ví dụ                                       |
|----------|------------------------------------|---------------------------------------------|
| create   | Tạo ví mới và sinh 12 từ khóa      | python main.py create --algo ecdsa        |
| recover  | Khôi phục ví từ 12 từ khóa         | python main.py recover --algo ed25519     |
| sign     | Ký một thông điệp/giao dịch        | python main.py sign "Transfer 10 ETH"     |
| info     | Xem thông tin ví đang lưu          | python main.py info                       |
| benchmark| Chạy bài test hiệu năng            | python main.py benchmark                  |

## 🎬 Kịch bản Demo (Dành cho báo cáo)

Sử dụng kịch bản này để trình bày các tính năng cốt lõi của ứng dụng.

### Tình huống 1: Người dùng mới (User Onboarding)

-   Mục tiêu: Chứng minh khả năng tạo ví và lưu trữ tự động.
-   Chạy lệnh: `python main.py create --algo ecdsa`

Kết quả:

-   Ứng dụng hiển thị 12 từ khóa bí mật.
-   Tạo địa chỉ ví Ethereum (0x...).
-   Thông báo đã lưu vào keystore.json.

Hành động: Lưu lại 12 từ khóa này ra file nháp.

### Tình huống 2: Thực hiện giao dịch (Signing)

-   Mục tiêu: Chứng minh tính năng Persistence (không cần nhập lại
    khóa).
-   Chạy lệnh: `python main.py sign "Gui 5 ETH cho Bob"`

Kết quả:

-   Ứng dụng tự động tải ví từ ổ cứng.
-   Hiển thị chữ ký số (Signature Hex) thành công.

### Tình huống 3: Giả lập mất ví & Khôi phục (Recovery)

-   Mục tiêu: Chứng minh tính an toàn và tất định của BIP-39.
-   Hành động: Xóa file keystore.json (giả lập mất máy).
-   Chạy lệnh: `python main.py recover --algo ecdsa`

Nhập liệu: Nhập 12 từ khóa đã lưu ở Tình huống 1.

Kết quả: Địa chỉ ví hiện ra trùng khớp hoàn toàn với địa chỉ ở Tình
huống 1. -\> Khôi phục thành công.

### Tình huống 4: Đa chuỗi (Cross-Chain)

-   Mục tiêu: Chứng minh 1 Seed dùng được cho nhiều mạng.
-   Chạy lệnh: `python main.py recover --algo ed25519` (Chuyển sang
    Solana)

Nhập liệu: Vẫn nhập 12 từ khóa cũ.

Kết quả: Ứng dụng tạo ra một địa chỉ ví hoàn toàn khác (dạng Hex trơn)
tương thích với mạng Solana, chứng minh khả năng HD Wallet.

### Tình huống 5: So sánh hiệu năng (Benchmark)

-   Mục tiêu: Phân tích kỹ thuật (Research).
-   Chạy lệnh: `python main.py benchmark`

Kết quả: Bảng so sánh hiện ra.

Nhận xét: Ed25519 và Schnorr thường nhanh hơn ECDSA đáng kể trong việc
tạo khóa và ký, phù hợp cho các Blockchain hiệu suất cao.

## ⚠️ Lưu ý bảo mật

Dự án này được xây dựng cho mục đích giáo dục và nghiên cứu (Educational
Purpose). Trong thực tế sản xuất (Production):

-   File keystore.json cần được mã hóa bằng mật khẩu người dùng
    (AES-256).
-   Không bao giờ hiển thị Private Key hoặc Mnemonic ra màn hình trừ lần

    đầu tiên tạo ví.

