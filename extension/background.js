chrome.action.onClicked.addListener((tab) => {
  if (tab.id && tab.url) {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: scrapeAndSendJob
    });
  }
});

async function scrapeAndSendJob() {
  const html = document.body.innerHTML;
  const url = window.location.href;
  
  try {
    const response = await fetch("http://localhost:8000/api/jobs/manual-ingest", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url, html })
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
