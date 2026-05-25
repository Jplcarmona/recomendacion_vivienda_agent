import undetected_chromedriver as uc
import platform
import tempfile
import time
import os

class BrowserManager:
    @staticmethod
    def create_driver(headless=False):
        options = uc.ChromeOptions()

        tmp_dir = os.path.join(
            tempfile.gettempdir(),
            f"chrome_profile_{int(time.time() * 1000)}"
        )
        os.makedirs(tmp_dir, exist_ok=True)
        options.add_argument(f"--user-data-dir={tmp_dir}")

        if headless:
            options.add_argument("--headless=new")

        # ← eliminado --start-maximized, conflicto con window-size en Windows
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # ← solo en Linux
        if platform.system() != "Windows":
            options.add_argument("--no-sandbox")

        # ← perfil temporal único por instancia
        tmp_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={tmp_dir}")

        options.add_argument(
            "--user-agent=Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/148.0.0.0 Safari/537.36"
        )

        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            version_main=148
        )

        driver.execute_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )

        return driver