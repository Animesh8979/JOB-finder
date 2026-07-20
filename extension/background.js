chrome.action.onClicked.addListener((tab) => {
  if (tab.id && tab.url) {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: scrapeAndSendJob
    });
  }
});

async function scrapeAndSendJob() {
  // Clone body and strip script/style/iframe tags to prevent XSS/injection over payload
  const clone = document.body.cloneNode(true);
  const elementsToRemove = clone.querySelectorAll("script, style, iframe, noscript, svg");
  elementsToRemove.forEach((el) => el.remove());

  const html = clone.innerHTML;
  const text = clone.innerText || clone.textContent || "";
  const url = window.location.href;
  const client_saved_at = new Date().toISOString();

  // Attempt to find posted date from DOM (<time> or JSON-LD)
  let dom_posted_at = null;
  const timeEl = document.querySelector("time[datetime]");
  if (timeEl) {
    dom_posted_at = timeEl.getAttribute("datetime");
  } else {
    const jsonLd = document.querySelector('script[type="application/ld+json"]');
    if (jsonLd) {
      try {
        const data = JSON.parse(jsonLd.textContent);
        dom_posted_at = data.datePosted || null;
      } catch (e) {}
    }
  }
  
  try {
    const response = await fetch("http://localhost:8000/api/jobs/manual-ingest", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url, html, text, dom_posted_at, client_saved_at })
    });
    
    if (response.ok) {
      alert("Job saved and scored successfully by AI Job Finder!");
    } else {
      const err = await response.json();
      alert("Error saving job: " + JSON.stringify(err));
    }
  } catch (error) {
    alert("Could not connect to local AI Job Finder server. Is it running on port 8000?");
  }
}
