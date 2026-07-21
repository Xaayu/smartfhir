export const GA_MEASUREMENT_ID =
  process.env.REACT_APP_GA_MEASUREMENT_ID ||
  process.env.REACT_APP_GA_ID ||
  (typeof window !== "undefined" && window.GA_MEASUREMENT_ID) ||
  "";

/**
 * Dynamically initialize Google Analytics 4 if measurement ID is present.
 */
export const initGA = () => {
  if (!GA_MEASUREMENT_ID) {
    return;
  }

  // Check if gtag script is already added
  if (document.getElementById("ga-gtag-script")) {
    return;
  }

  // Inject Google Tag script
  const script = document.createElement("script");
  script.id = "ga-gtag-script";
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script);

  // Setup dataLayer and gtag function
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    window.dataLayer.push(arguments);
  }
  window.gtag = gtag;

  gtag("js", new Date());
  gtag("config", GA_MEASUREMENT_ID, {
    send_page_view: false, // Page views handled via React Router hook
  });
};

/**
 * Track page view hit to Google Analytics
 * @param {string} path - URL path (e.g. /tools/fhir)
 * @param {string} [title] - Page title
 */
export const trackPageView = (path, title) => {
  if (!GA_MEASUREMENT_ID) return;

  if (typeof window.gtag === "function") {
    window.gtag("config", GA_MEASUREMENT_ID, {
      page_path: path,
      page_title: title || document.title,
    });
  }
};

/**
 * Track custom event in Google Analytics
 * @param {string} action - Event name (e.g., 'generate_api_key')
 * @param {Object} [params] - Additional event parameters
 */
export const trackEvent = (action, params = {}) => {
  if (!GA_MEASUREMENT_ID) return;

  if (typeof window.gtag === "function") {
    window.gtag("event", action, params);
  }
};
