import smtp
import download_email



if __name__ == '__main__':
    while True:
        print("Vui lòng lựa chọn: ")
        print("1. Gửi email")
        print("2. Đọc email")
        print("3. Thoát")

        choice = input("Chọn: ")
        if not choice:
            print('Giá trị không hợp lệ')
            continue
        elif choice == '1':
            smtp.main()
        elif choice == '2':
            download_email.read_email()
        elif choice == '3':
            break
        else:
            print('Giá trị không hợp lệ !!!')