import csv
import os

class FinanceTracker:
    def __init__(self):
        self.balance = 0
        self.transactions = []
        self.csv_file_path = 'master_transactions.csv'
        self.load_data

    def load_data(self):
        if os.path.exists(self.csv_file):
            with open(self.csv_file, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self.transactions.append({
                        "description": row['Description'],
                        "amount": float(row['Amount'])
                    })
                    self.balance += float(row['Amount'])

    def add_transaction(self, description, amount):
        self.transactions.append({"description": description, "amount": amount})
        self.balance += amount

    def view_balance(self):
        return self.balance

    def view_transactions(self):
        return self.transactions


# Main function to interact with the finance tracker
def main():
    tracker = FinanceTracker()

    while True:
        print("\nFinance Tracker Menu:")
        print("1. Add Transaction")
        print("2. View Balance")
        print("3. View Transactions")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            description = input("Enter transaction description: ")
            amount = float(input("Enter transaction amount: "))
            tracker.add_transaction(description, amount)
            print("Transaction added successfully!")
        elif choice == "2":
            print("Current Balance: ${:.2f}".format(tracker.view_balance()))
        elif choice == "3":
            transactions = tracker.view_transactions()
            print("\nTransaction History:")
            for transaction in transactions:
                print("- {} ${:.2f}".format(transaction["description"], transaction["amount"]))
        elif choice == "4":
            print("Exiting Finance Tracker. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()