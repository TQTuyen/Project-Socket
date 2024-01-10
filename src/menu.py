import smtp1
import download_email



if __name__ == '__main__':
    while True:
        print("Please choose your selection:")
        print("1. Send email")
        print("2. Read list email")
        print("3. Exit")

        choice = int(input("Choose: "))
        if choice == 1:
            smtp1.main()
        elif choice == 2:
            download_email.read_email()
        elif choice == 3:
            break
        else:
            print('Invalid')