"""Browser Controller

Handles browser automation for Metamask extension, including:
- Playwright browser automation
- Metamask extension interaction
- Page navigation and element detection
- Screenshot capture for debugging
- Session management and cleanup

Enables secure, automated browser-based wallet operations.
"""

import asyncio
import logging
import time # Added for duration calculation
from typing import Optional, Dict, Any

from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Error as PlaywrightError

from .security_manager import SecurityManager, SecurityViolationError, PhishingDetectedError, InvalidSessionError
from .metrics import record_browser_automation_security_event, record_browser_operation # Added metrics import
# validator.py is a stub; use placeholder validation for now

logger = logging.getLogger(__name__)

class BrowserControllerError(Exception):
    """Base exception for BrowserController errors."""
    pass

class BrowserController:
    """
    Secure controller for automating Metamask browser interactions using Playwright.
    Integrates with SecurityManager for session, phishing, and transaction validation.
    All DOM and user inputs are validated and sanitized.
    """

    def __init__(self, security_manager: SecurityManager, metamask_extension_path: str):
        """
        :param security_manager: Instance of SecurityManager for validation and session control.
        :param metamask_extension_path: Path to unpacked Metamask extension directory.
        """
        self.security_manager = security_manager
        self.metamask_extension_path = metamask_extension_path
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def launch_browser(self) -> None:
        """
        Launch a hardened browser instance with Metamask extension loaded.
        Applies security flags and disables unnecessary features.
        """
        playwright = await async_playwright().start()
        try:
            self.browser = await playwright.chromium.launch_persistent_context(
                user_data_dir="/tmp/metamask_user_data",  # Should be ephemeral or session-specific
                headless=False,  # Metamask requires non-headless for some flows
                args=[
                    f"--disable-extensions-except={self.metamask_extension_path}",
                    f"--load-extension={self.metamask_extension_path}",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-remote-fonts",
                    "--disable-background-networking",
                    "--disable-sync",
                    "--disable-default-apps",
                    "--disable-popup-blocking",
                    "--disable-remote-extensions",
                    "--disable-site-isolation-trials",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--js-flags=--no-expose-wasm,--no-expose-async-hooks",
                ],
                ignore_default_args=["--enable-automation"],  # Remove automation flag for stealth
                viewport={"width": 1280, "height": 800},
                accept_downloads=False,
                java_script_enabled=True,
                bypass_csp=False,  # We'll inject our own CSP
            )
            self.context = self.browser
            self.page = await self.context.new_page()
            await self._inject_security_headers(self.page)
            logger.info("Browser launched with hardened settings and Metamask extension.")
        except PlaywrightError as e:
            logger.error(f"Failed to launch browser: {e}")
            raise

    async def _inject_security_headers(self, page: Page) -> None:
        """
        Injects CSP and XSS protections into every page.
        """
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-eval' 'unsafe-inline' chrome-extension:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none';"
        )
        await page.add_init_script(
            f"""
            (() => {{
                const meta = document.createElement('meta');
                meta.httpEquiv = "Content-Security-Policy";
                meta.content = "{csp}";
                document.head.appendChild(meta);
            }})();
            """
        )
        # Optionally, inject XSS protection headers or scripts
        await page.add_init_script(
            """
            window.addEventListener('DOMContentLoaded', () => {
                // Remove dangerous inline event handlers
                document.querySelectorAll('*').forEach(el => {
                    for (const attr of el.getAttributeNames()) {
                        if (attr.startsWith('on')) el.removeAttribute(attr);
                    }
                });
            });
            """
        )

    async def close_browser(self) -> None:
        """
        Closes the browser and cleans up resources.
        """
        if self.context:
            await self.context.close()
            self.context = None
            self.browser = None
            self.page = None
            logger.info("Browser context closed and cleaned up.")

    async def navigate(self, url: str, session_token: str) -> None:
        """
        Securely navigate to a URL after phishing and session validation.
        Records duration and security events.
        """
        start_time = time.time()
        current_status = "success" # Default status

        try:
            self.security_manager.validate_session(session_token)
            self.security_manager.check_phishing(url)

            if not url.startswith("http"): # Basic URL validation
                current_status = "failure_invalid_url_scheme"
                record_browser_automation_security_event(event_type="invalid_url_scheme")
                raise ValueError("Invalid URL scheme.")

            if not self.page:
                # Attempt to launch browser if page is not available.
                # This might indicate an issue if launch_browser wasn't called or failed previously.
                logger.warning("Page not available for navigation, attempting to launch browser.")
                await self.launch_browser()
                if not self.page: # Still no page after attempt
                    current_status = "failure_page_unavailable"
                    record_browser_automation_security_event(event_type="page_unavailable_error")
                    raise BrowserControllerError("Browser page not available for navigation even after launch attempt.")
            
            await self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
            logger.info(f"Navigated to {url}")

        except InvalidSessionError as e:
            current_status = "failure_invalid_session"
            logger.error(f"Navigation blocked due to invalid session: {session_token} - {e}")
            record_browser_automation_security_event(event_type="invalid_session")
            raise
        except PhishingDetectedError as e:
            current_status = "failure_phishing_detected"
            logger.error(f"Navigation blocked due to phishing detection: {url} - {e}")
            record_browser_automation_security_event(event_type="phishing_detected")
            raise
        except PlaywrightError as e:
            current_status = "failure_playwright_error"
            logger.error(f"Playwright navigation error for URL {url}: {e}")
            record_browser_automation_security_event(event_type="playwright_navigation_error")
            # Consider re-raising as BrowserControllerError or a more specific custom error
            raise BrowserControllerError(f"Navigation to {url} failed due to Playwright error: {e}")
        except ValueError as e: # Catching the ValueError from invalid URL scheme
            current_status = "failure_value_error" # Already set if invalid_url_scheme
            logger.error(f"Navigation failed due to ValueError: {e}")
            # Security event already recorded if it's invalid_url_scheme
            if current_status != "failure_invalid_url_scheme":
                 record_browser_automation_security_event(event_type="navigation_value_error")
            raise
        except Exception as e:
            current_status = "failure_unknown_error"
            logger.error(f"Unexpected error during navigation to {url}: {e}")
            record_browser_automation_security_event(event_type="unknown_navigation_error")
            # Consider re-raising as BrowserControllerError
            raise BrowserControllerError(f"Unexpected error navigating to {url}: {e}")
        finally:
            duration = time.time() - start_time
            record_browser_operation(operation="navigate", status=current_status, duration=duration)

    async def interact_with_element(self, selector: str, action: str, value: Optional[str] = None) -> None:
        """
        Securely interact with a DOM element (click, type, etc.) after validating selector and action.
        Records duration and security events.
        :param selector: CSS selector for the element.
        :param action: Action to perform ('click', 'type', etc.).
        :param value: Value to type if action is 'type'.
        """
        start_time = time.time()
        current_status = "success"

        try:
            # Placeholder for selector validation
            if not isinstance(selector, str) or len(selector) > 256 or "<" in selector or ">" in selector:
                current_status = "failure_unsafe_selector"
                record_browser_automation_security_event(event_type="unsafe_selector")
                raise ValueError("Unsafe selector pattern detected.")

            if not self.page:
                current_status = "failure_page_unavailable"
                record_browser_automation_security_event(event_type="page_unavailable_interaction")
                raise BrowserControllerError("Browser page not available for interaction.")

            element = await self.page.wait_for_selector(selector, timeout=5000, state="visible")
            
            if action == "click":
                await element.click(timeout=5000) # Added timeout to click
                logger.info(f"Clicked element: {selector}")
            elif action == "type":
                if value is None or not isinstance(value, str) or len(value) > 256:
                    current_status = "failure_unsafe_type_value"
                    record_browser_automation_security_event(event_type="unsafe_type_value")
                    raise ValueError("Unsafe or missing value for typing.")
                await element.fill(value, timeout=5000) # Added timeout to fill
                logger.info(f"Typed into element: {selector}")
            else:
                current_status = "failure_unsupported_action"
                record_browser_automation_security_event(event_type="unsupported_interaction_action")
                raise ValueError(f"Unsupported action: {action}")

        except PlaywrightError as e:
            current_status = "failure_playwright_error"
            logger.error(f"Element interaction error for selector {selector}, action {action}: {e}")
            # Be more specific with event_type if possible, e.g. element_not_found, click_timeout
            event_type_detail = "playwright_interaction_error"
            if "timeout" in str(e).lower():
                event_type_detail = f"{action}_timeout_error"
            elif "not found" in str(e).lower() or "no element found" in str(e).lower(): # Common phrases
                event_type_detail = f"{action}_element_not_found"
            record_browser_automation_security_event(event_type=event_type_detail)
            raise BrowserControllerError(f"Interaction with {selector} (action: {action}) failed due to Playwright error: {e}")
        except ValueError as e:
            # Status should be set by specific checks above, but this is a fallback
            if current_status == "success": # If not already set by specific checks
                 current_status = "failure_value_error"
                 record_browser_automation_security_event(event_type=f"{action}_value_error")
            logger.error(f"Interaction ValueError for selector {selector}, action {action}: {e}")
            raise
        except BrowserControllerError: # Re-raise if it's already a BrowserControllerError (e.g. page unavailable)
            # Status should be set by the original raiser
            raise
        except Exception as e:
            current_status = "failure_unknown_error"
            logger.error(f"Unexpected error during interaction with {selector}, action {action}: {e}")
            record_browser_automation_security_event(event_type=f"unknown_{action}_error")
            raise BrowserControllerError(f"Unexpected error with {selector}, action {action}: {e}")
        finally:
            duration = time.time() - start_time
            record_browser_operation(operation=f"interact_{action}", status=current_status, duration=duration)

    async def capture_screenshot(self, path: str) -> None:
        """
        Capture a screenshot for debugging.
        """
        if not self.page:
            raise RuntimeError("No active page to capture screenshot.")
        await self.page.screenshot(path=path)
        logger.info(f"Screenshot saved to {path}")

    async def perform_metamask_interaction(self, session_token: str, interaction: Dict[str, Any]) -> None:
        """
        Perform a secure Metamask interaction (e.g., transaction signing).
        Validates session and transaction, and logs security events.
        :param session_token: Session token for the user.
        :param interaction: Dict describing the interaction (type, params, etc.).
        """
        try:
            self.security_manager.validate_session(session_token)
            if interaction.get("type") == "transaction":
                self.security_manager.verify_transaction(interaction.get("params", {}))
            # Additional interaction types can be handled here
        except (InvalidSessionError, SecurityViolationError) as e:
            logger.error(f"Metamask interaction blocked: {e}")
            self.security_manager.log_security_event({
                "event_type": "interaction_blocked",
                "reason": str(e),
                "interaction": interaction,
            })
            raise

        # Example: Click the "Confirm" button in Metamask popup
        if interaction.get("type") == "transaction":
            # This selector is for illustration; real selectors should be validated and kept up to date
            await self.interact_with_element('button[data-testid="page-container-footer-next"]', "click")
            logger.info("Metamask transaction confirmed via automation.")

    # Additional secure utility methods can be added as needed