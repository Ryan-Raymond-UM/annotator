function toggleInputFields() {
    const inputMethod = document.getElementById('inputMethod').value;
    const zipInput = document.getElementById('zipInput');
    const pathInput = document.getElementById('pathInput');
    
    const fileUpload = document.getElementById('fileUpload'); // For ZIP file input
    const folderPath = document.getElementById('folderPath'); // For folder path

    if (inputMethod === 'zip') {
        zipInput.style.display = 'block';
        pathInput.style.display = 'none';
        // Reset the file input for ZIP file upload
        fileUpload.value = ""; 
        folderPath.value = "";
    } else {
        zipInput.style.display = 'none';
        pathInput.style.display = 'block';
        // Reset the path input
        fileUpload.value = ""; 
        folderPath.value = "";
    }
}


 // Function to show/hide encoding model dropdowns based on input type
    function toggleEncodingDropdowns() {
        var inputType = document.getElementById('inputType').value;
        var imageEncodingDiv = document.getElementById('imageEncodingDiv');
        var textEncodingDiv = document.getElementById('textEncodingDiv');

        if (inputType === 'image') {
            imageEncodingDiv.style.display = 'block';
            textEncodingDiv.style.display = 'none';
        } else if (inputType === 'text') {
            imageEncodingDiv.style.display = 'none';
            textEncodingDiv.style.display = 'block';
        } else {
            imageEncodingDiv.style.display = 'block';
            textEncodingDiv.style.display = 'block';
        }
    }

// Initial call to set the correct dropdowns visibility
toggleEncodingDropdowns();


// Function to validate the inputs
    function validateInputs(event) {

        console.log( "came in validate inputs" );
        
        var zipInput = document.getElementById('fileUpload');
        var pathInput = document.getElementById('folderPath');

        if (  (zipInput.value.trim() == "") && (pathInput.value.trim() == "")  ) {
            // If neither is filled, prevent form submission and alert the user
            event.preventDefault();
            alert('Please either upload a ZIP file or enter a folder path.');
            return false;
        }
        
        return true;
}



document.addEventListener("DOMContentLoaded", function () {
    const downloadButtons = document.querySelectorAll(".download-btn");
    const loader = document.getElementById("loader");

    downloadButtons.forEach(button => {
        button.addEventListener("click", function (e) {
            e.preventDefault();

            const jobId = this.getAttribute("data-job-id");
            const downloadUrl = `/download?id=${jobId}`;

            // Show loader
            loader.style.display = "block";

            // Create a temporary invisible iframe to trigger download
            const iframe = document.createElement("iframe");
            iframe.style.display = "none";
            iframe.src = downloadUrl;
            document.body.appendChild(iframe);

            // Hide loader after a fixed delay (optional fallback)
            setTimeout(() => {
                loader.style.display = "none";
                iframe.remove();
            }, 10000); // 10 seconds fallback (you can adjust this)
        });
    });
});