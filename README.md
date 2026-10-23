<div align="center">

# 📊 CPE 010 – Data Structures and Algorithms

### *Course Portfolio • Laboratory Activities • Projects*

<img src="https://img.shields.io/badge/Technological%20Institute%20of%20the%20Philippines-CPE%009B-blue?style=for-the-badge"/>

<img src="https://img.shields.io/badge/Language-Python-yellow?style=for-the-badge&logo=python&logoColor=white"/>

<img src="https://img.shields.io/badge/Status-%20Finished-success?style=for-the-badge"/>

<br><br>

---

# 👋 Hello! We're **Group 1!**

### 🎓 Computer Engineering Students

**Technological Institute of the Philippines – Quezon City**

</div>

---

# Project Algorithm

Start System
Cashier log-in
Start Transaction
Generate Transaction Number
Cashier enters item id / click item (Both applicable)
System search
If found, show the item name, image, and price in pesos, then ask for the quantity. If not found, show "Item not found" and go back to step 3.
Add the item to the cart and update the running subtotal.
Repeat steps 3 to 6 until all items are entered.
Ask for the customer type (Regular, Senior, PWD, or other promo).
Apply the discount: Senior/PWD get a fixed 20% off, and other promos get their own % off.
Compute the 12% VAT on the discounted total.
Compute the final total and accept payment and change.
Generate and print the receipt, then end the transaction

---

# Project Pseudocode

START
  DISPLAY logo
  CREATE new transaction, assign transaction number
  SET cart to empty

  REPEAT
    INPUT serial number
    SEARCH item list using serial number
    IF item exists THEN
      DISPLAY name, image, price (PHP)
      INPUT quantity
      ADD item to cart
      COMPUTE subtotal
    ELSE
      DISPLAY "Item not found"
    ENDIF
  UNTIL cashier selects "Checkout"

  INPUT customer type
  IF customer is Senior or PWD THEN
    discount = subtotal x 20%
  ELSE IF promo applies THEN
    discount = subtotal x promo %
  ELSE
    discount = 0
  ENDIF

  net amount = subtotal - discount
  VAT (12%) = net amount / 1.12 x 0.12
  total = net amount

  INPUT payment
  change = payment - total

  PRINT receipt (transaction no., date/time, store name/address,
                 items, discount, VAT, total, payment, change)
END


---

# 🗂️ Course Topics

## 📘 Prelim

-
-

## 📙 Midterm

-
-


## 📗 Final

-
-


---

# 💻 Programming Language

<div align="center">

<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" width="90"/>

### Python

</div>

---

# 🛠️ Tools & Technologies

<div align="center">

<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" width="70" alt="Python"/>

<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/git/git-original.svg" width="70" alt="Git"/>

<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/github/github-original.svg" width="70" alt="GitHub"/>

<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/vscode/vscode-original.svg" width="70" alt="VS Code"/>

</div>

<div align="center">

| Technology | Purpose |
|------------|---------|
| 🐍 C++ | DSA |
| 📝 VS Code | Code Editor |
| 🌿 Git | Version Control |
| 📂 GitHub | Repository Hosting |

</div>

---

# 📂 Repository Structure

```text
CPE 009B – Object Oriented Programming 2
│
├── 📁 Project FIles
└── 📄 README.md
```

---

# 📧 Contact Us

**TIP Emails**

📩 qpbvillaruel25@tip.edu.ph
📩 qmjbautista25@tip.edu.ph
📩 qecruz@tip.edu.ph
📩 qjbbarizo@tip.edu.ph
📩 qcfernadez@tip.edu.ph
📩 qnmendoza@tip.edu.ph

---

<div align="center">

## ⭐ Thank You for Visiting!


</div>
