 <div align="center">

#  CPE 009B – Object-Oriented Programming 2


![TIP](https://img.shields.io/badge/Technological%20Institute%20of%20the%20Philippines-CPE%20009B-blue?style=for-the-badge)

![Status](https://img.shields.io/badge/Status-Completed-success?style=for-the-badge)

---

# 👋 Hello! Welcome to EcoBasket Supermarket!

<img width="673" height="643" alt="LOGO" src="https://github.com/user-attachments/assets/5e8e43c1-f3a2-4d64-a7dc-2bb4788372a4" />

### Presented by Computer Engineering Students

**At the Technological Institute of the Philippines – Quezon City**

</div>

---

# 🧾 Project Algorithm

1. Start the system.
2. Display the system logo and cashier login screen.
3. Authenticate the cashier.
4. Start a new transaction and generate a transaction number.
5. Allow the cashier to enter an item ID or select an item from the product list.
6. Search for the selected item in the database.
7. If the item exists, display its name, image, and price in Philippine pesos (PHP), then ask for the quantity.
8. If the item does not exist, display **"Item not found"** and return to item selection.
9. Add the item to the cart and update the running subtotal.
10. Repeat the item selection process until the cashier chooses Checkout.
11. Ask for the customer's type: Regular, Senior Citizen, PWD, or applicable promotional category.
12. Apply the appropriate discount: 20% for eligible Senior Citizens and PWD customers, or the applicable promotional discount.
13. Calculate the VAT and final amount according to the applicable tax rules.
14. Accept the customer's payment and calculate the change.
15. Generate and print the receipt containing the transaction details.
16. End the transaction and return to the cashier interface.

---

# 📝 Project Pseudocode

```text
START

    DISPLAY system logo
    AUTHENTICATE cashier

    IF login is successful THEN

        CREATE new transaction
        GENERATE transaction number
        SET cart = empty
        SET subtotal = 0

        REPEAT
            INPUT item ID or select item
            SEARCH item database

            IF item exists THEN
                DISPLAY item name, image, and price
                INPUT quantity

                IF quantity > 0 THEN
                    ADD item and quantity to cart
                    UPDATE subtotal
                ELSE
                    DISPLAY "Invalid quantity"
                ENDIF

            ELSE
                DISPLAY "Item not found"
            ENDIF

        UNTIL cashier selects Checkout

        INPUT customer type

        IF customer is eligible for Senior/PWD discount THEN
            discount = eligible amount x 20%
        ELSE IF promotional discount applies THEN
            discount = eligible amount x promo rate
        ELSE
            discount = 0
        ENDIF

        CALCULATE applicable VAT
        CALCULATE final total

        INPUT payment

        WHILE payment < final total
            DISPLAY "Insufficient payment"
            INPUT payment
        ENDWHILE

        change = payment - final total

        GENERATE receipt containing:
            Transaction number
            Date and time
            Store name and address
            Purchased items and quantities
            Subtotal and discount
            VAT
            Final total
            Payment and change

        PRINT receipt

    ELSE
        DISPLAY "Invalid login"
    ENDIF

END
```

# Implementation of OOP

<img width="617" height="284" alt="ImplementOOP" src="https://github.com/user-attachments/assets/5f8c217c-ff43-4301-8dbf-b81a4a470c3c" />

---

# 💻 Programming Language

<div align="center">

<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" width="90" alt="Python Logo"/>

### Python

</div>

---

# 🛠️ Tools & Technologies

<div align="center">

<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" width="65" alt="Python"/>&nbsp;&nbsp;
<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/git/git-original.svg" width="65" alt="Git"/>&nbsp;&nbsp;
<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/github/github-original.svg" width="65" alt="GitHub"/>&nbsp;&nbsp;
<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/vscode/vscode-original.svg" width="65" alt="Visual Studio Code"/>

</div>

| Technology | Purpose |
|---|---|
| 🐍 Python | Primary programming language |
| 📝 Visual Studio Code | Code editor |
| 🌿 Git | Version control |
| 📂 GitHub | Repository hosting and collaboration |

---

# 📂 Repository Structure

```text
CPE 009B – Object-Oriented Programming 2
│
├── 📁 Project Files/
│   └── Source code and project resources
│
└── 📄 README.md
```

---

# 📧 Contact Us

**TIP Student Emails**

- 📩 qpbvillaruel25@tip.edu.ph
- 📩 qmjbautista25@tip.edu.ph
- 📩 qecruz@tip.edu.ph
- 📩 qjbbarizo@tip.edu.ph
- 📩 qcfernadez@tip.edu.ph
- 📩 qnmendoza@tip.edu.ph

---

<div align="center">

## ⭐ Thank You for Visiting!

*Developed by Group 1 – Computer Engineering Students*

**Technological Institute of the Philippines – Quezon City**

</div>
