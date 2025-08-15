document.addEventListener("DOMContentLoaded", function () {
    const downloadButtons = document.querySelectorAll(".download-btn");
    const loader = document.getElementById("loader");
    const loaderText = document.getElementById("loader-text");
    const progressBar = document.getElementById("progress-bar");

    downloadButtons.forEach(button => {
        button.addEventListener("click", async function (e) {
            e.preventDefault();

            const confirmed = confirm("Do you want to download the data?");
            if (!confirmed) return;

            const jobId = this.getAttribute("data-job-id");

            // Show loader UI
            showLoader("Preparing your download...");

            try {
                // Step 1: Trigger preparation
                const prepResponse = await fetch(`/prepare-download?id=${jobId}`, {
                    method: "POST"
                });

                if (!prepResponse.ok) {
                    throw new Error("Failed to start preparation");
                }

                // Step 2: Poll status
                pollStatus(jobId);

            } catch (err) {
                hideLoader();
                alert("Error while preparing download: " + err.message);
            }
        });
    });

    function showLoader(message) {
        loader.style.display = "block";
        loaderText.innerText = message;
        updateProgress(0);
        document.getElementById("page-content")?.classList.add("blur");
    }
    
    function hideLoader() {
        loader.style.display = "none";
        document.getElementById("page-content")?.classList.remove("blur");
    }

    function updateProgress(percent) {
        progressBar.style.width = percent + "%";
        progressBar.setAttribute("aria-valuenow", percent);
        progressBar.innerText = percent + "%";
    }

    async function pollStatus(jobId) {
        const pollInterval = 2000; // 2 seconds
        const maxAttempts = 60; // 2 minutes max
        let attempts = 0;

        const intervalId = setInterval(async () => {
            attempts++;

            try {
                const res = await fetch(`/download-status?id=${jobId}`);
                const data = await res.json();

                if (data.status === "ready") {
                    updateProgress(100);
                    clearInterval(intervalId);
                    triggerDownload(jobId);
                    setTimeout(hideLoader, 2000);
                } else if (data.status === "preparing") {
                    updateProgress(data.progress || 0);
                } else if (data.status === "error") {
                    clearInterval(intervalId);
                    hideLoader();
                    alert("Error: " + (data.message || "An error occurred."));
                }

                if (attempts >= maxAttempts) {
                    clearInterval(intervalId);
                    hideLoader();
                    alert("Timed out while preparing download.");
                }

            } catch (err) {
                clearInterval(intervalId);
                hideLoader();
                alert("Error checking progress: " + err.message);
            }

        }, pollInterval);
    }

    function triggerDownload(jobId) {
        const downloadUrl = `/download?id=${jobId}`;
        const iframe = document.createElement("iframe");
        iframe.style.display = "none";
        iframe.src = downloadUrl;
        document.body.appendChild(iframe);

        // Remove iframe after a short delay
        setTimeout(() => {
            iframe.remove();
        }, 10000);
    }
});



// document.addEventListener("DOMContentLoaded", function () {
//     const downloadButtons = document.querySelectorAll(".download-btn");
//     const loader = document.getElementById("loader");
//     const content = document.getElementById("page-content");

//     downloadButtons.forEach(button => {
//         button.addEventListener("click", function (e) {
//             e.preventDefault();

//             const jobId = this.getAttribute("data-job-id");
//             const downloadUrl = `/download?id=${jobId}`;

//             // Show loader and blur background
//             loader.style.display = "block";
//             content.classList.add("blur");

//             // Create a temporary invisible iframe to trigger download
//             const iframe = document.createElement("iframe");
//             iframe.style.display = "none";
//             iframe.src = downloadUrl;
//             document.body.appendChild(iframe);

//             // Hide loader after delay (fallback)
//             setTimeout(() => {
//                 loader.style.display = "none";
//                 content.classList.remove("blur");
//                 iframe.remove();
//             }, 10000); // Adjust duration as needed
//         });
//     });
// });