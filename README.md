# VisuaLexUI

![Version](https://img.shields.io/badge/version-0.0.5-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Contributions](https://img.shields.io/badge/contributions-welcome-orange)

VisuaLexUI is a Python-based graphical user interface (GUI) application built with PyQt6. It allows users to search for and view legal norms, customize interface themes, and manage API interactions for retrieving legal data.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Usage](#usage)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Search Legal Norms:** Search for legal norms by type, date, article number, and version (original or current).
- **Customizable Themes:** Customize the application’s appearance using a built-in theme dialog.
- **API Integration:** Fetch data from a remote API (VisuaLexAPI) with error handling, retries, and caching.
- **Brocardi Information Display:** View detailed legal metadata, including information from the website brocardi.com.

## Getting Started

To get started with VisuaLexUI, follow the installation instructions below and run the application to explore its features.

## Installation

Follow these steps to set up the application on your local machine:

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/capazme/VisuaLexUI.git
    cd VisuaLexUI
    ```

2. **Create a Virtual Environment:**

   Ensure Python 3.7+ is installed. You can check if Python is installed by running:

    ```bash
    python3 --version
    ```

   Then, create a Python virtual environment using `venv`:

    ```bash
    python3 -m venv .venv
    ```

   Activate the virtual environment:

   - **On Linux/macOS:**

    ```bash
    source .venv/bin/activate
    ```

   - **On Windows:**

    ```bash
    .venv\Scripts\activate
    ```

3. **Install Dependencies:**

   Install the required dependencies using `pip`:

    ```bash
    pip install -r requirements.txt
    ```

4. **Build the Application:**

   To build the application, run the appropriate script for your operating system:

   - **On Windows:**

    ```bash
    build.bat
    ```

   - **On macOS/Linux:**

    ```bash
    bash build.sh
    ```

   The built application will be located in the directory.

## Usage

- **Search Interface:** Use the input fields to search for legal norms by type, date, act number, and article number.
- **Theme Customization:** Navigate to "Settings" > "Customize Theme" to adjust the application's theme.
- **API URL Management:** Modify the API URL through "Settings" > "Change API URL" to set a new VisuaLexAPI endpoint.


## Dependencies

- **Python 3.7+**
- **PyQt6**
- **Requests**
- **Other libraries:** Listed in `requirements.txt`

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. **Fork the repository.**
2. **Create a new branch** for your feature (`git checkout -b feature/AmazingFeature`).
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`).
4. **Push to the branch** (`git push origin feature/AmazingFeature`).
5. **Open a Pull Request.**

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute this software. See the [LICENSE](LICENSE) file for more details.

## Contact

For more information, feel free to reach out to the project maintainer:

- GitHub: [capazme](https://github.com/capazme)
