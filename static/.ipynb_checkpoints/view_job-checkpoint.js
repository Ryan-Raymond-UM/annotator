
document.addEventListener('DOMContentLoaded', function () {
    
  const dropdowns = document.querySelectorAll('.custom-category-dropdown');

  const jobId = document.querySelector('.card-title')?.textContent.trim().replace('Job ID: ', '');

  dropdowns.forEach(function (dropdown) {
    // Skip the global dropdown
    if (dropdown.classList.contains('global-category-dropdown')) {
      return;
    }

    const dropdownLabel = dropdown.querySelector('.dropdown-label');
    const hiddenInput = dropdown.parentElement.querySelector('.selected-category');
    const categoryOptions = dropdown.querySelectorAll('.category-option');
    const otherInput = dropdown.querySelector('.other-category-input');
    const imageElement = dropdown.closest('.col-md-3')?.querySelector('img');
    const imageUrl = imageElement?.getAttribute('src');

    if (!otherInput || !imageUrl) return;

    let lastSentCategory = '';

    categoryOptions.forEach(function (option) {
      option.addEventListener('click', function (e) {
        e.preventDefault();
        const value = this.textContent.trim();
        dropdownLabel.textContent = value;
        hiddenInput.value = value;
        otherInput.value = ''; // Clear custom input

        if (value !== lastSentCategory) {
          sendCategoryUpdate(jobId, imageUrl, value, "add", "dropdown");
          lastSentCategory = value;
        }
      });
    });

    // Send update on input with debounce
    let debounceTimer;
    otherInput.addEventListener('input', function () {
      const value = this.value.trim();
      dropdownLabel.textContent = value || 'Other (specify)';
      hiddenInput.value = value;

      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        if (value && value !== lastSentCategory) {
          sendCategoryUpdate(jobId, imageUrl, value, "add", "dropdown" );
          lastSentCategory = value;
        }
      }, 500);
    });

    // Optional: also send on blur
    otherInput.addEventListener('blur', function () {
      const value = this.value.trim();
      dropdownLabel.textContent = value || 'Other (specify)';
      hiddenInput.value = value;

      if (value && value !== lastSentCategory) {
        sendCategoryUpdate(jobId, imageUrl, value, "add", "dropdown");
        lastSentCategory = value;
      }
    });
  });

  
});





function updateCountsDropdown(counts, newF1Score, newAccuracy) {
    const dropdownMenu = document.getElementById('counts-dropdown-menu');
    if (!dropdownMenu) return;
    
    // Clear and rebuild
    dropdownMenu.innerHTML = '';
    
    // Add the search input
    const searchItem = document.createElement('li');
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'form-control mb-2 dropdown-search';
    searchInput.placeholder = 'Search...';
    searchItem.appendChild(searchInput);
    dropdownMenu.appendChild(searchItem);

    let totalCount = null;
    let totalLabel = null;
    
    // Add the category items (except Total)
    for (const category in counts) {
      const count = counts[category];
    
      if (category.startsWith('Total')) {
        totalCount = count; // Save Total for later
        totalLabel = category
        continue; // Skip adding it now
      }
    
      const listItem = document.createElement('li');
      const link = document.createElement('a');
      link.className = 'dropdown-item category-option';
      link.href = '#';
      link.textContent = `${category} – ${count}`;
      listItem.appendChild(link);
      dropdownMenu.appendChild(listItem);
    }
    
    // Insert <hr> and Total before F1-Score
    if (totalCount !== null) {
      const hr = document.createElement('hr');
      dropdownMenu.appendChild(hr);
    
      const totalItem = document.createElement('li');
      const totalLink = document.createElement('a');
      totalLink.className = 'dropdown-item';
      totalLink.href = '#';
      totalLink.textContent = `${totalLabel} – ${totalCount}`;
      totalItem.appendChild(totalLink);
      dropdownMenu.appendChild(totalItem);
    }


    // Add F1-Score to dropdown
    const f1Item = document.createElement('li');
    const f1Link = document.createElement('a');
    f1Link.className = 'dropdown-item';
    f1Link.href = '#';
    f1Link.textContent = `F1-Score – ${newF1Score}`;
    f1Item.appendChild(f1Link);
    dropdownMenu.appendChild(f1Item);
    
    // Add Accuracy to dropdown
    const accItem = document.createElement('li');
    const accLink = document.createElement('a');
    accLink.className = 'dropdown-item';
    accLink.href = '#';
    accLink.textContent = `Accuracy – ${newAccuracy}`;
    accItem.appendChild(accLink);
    dropdownMenu.appendChild(accItem);

  // Re-bind the search filter functionality
  searchInput.addEventListener('keyup', function () {
    const filter = this.value.toLowerCase();
    dropdownMenu.querySelectorAll('.dropdown-item').forEach(function (item) {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(filter) ? '' : 'none';
    });
  });
}




document.addEventListener('DOMContentLoaded', function () {
// Single function for all dropdown search inputs
document.querySelectorAll('.dropdown-search').forEach(function (input) {
  input.addEventListener('keyup', function () {
	const filter = this.value.toLowerCase();
	const dropdownMenu = this.closest('.dropdown-menu');

	dropdownMenu.querySelectorAll('.dropdown-item').forEach(function (item) {
	  const text = item.textContent.toLowerCase();
	  item.style.display = text.includes(filter) ? '' : 'none';
	});
  });
});
});



document.addEventListener('DOMContentLoaded', function () {
  const jobId = document.querySelector('.card-title')?.textContent.trim().replace('Job ID: ', '');


  // ================
  // Global Dropdown
  // ================
  const globalDropdown = document.querySelector('.global-category-dropdown');

  if (globalDropdown) {
    const globalLabel = globalDropdown.querySelector('.dropdown-label');
    const globalOptions = globalDropdown.querySelectorAll('.category-option');

    globalOptions.forEach(function (option) {
      option.addEventListener('click', function (e) {
        e.preventDefault();

        const selectedValue = this.textContent.trim();
        globalLabel.textContent = selectedValue;

        const imageUrlsToUpdate = [];

        // Select all individual dropdowns
        const dropdowns = document.querySelectorAll('.custom-category-dropdown:not(.global-category-dropdown)');

        dropdowns.forEach(function (dropdown) {
          const imageElement = dropdown.closest('.col-md-3')?.querySelector('img');
          const imageUrl = imageElement?.getAttribute('src');


          // Extract image path from query string
          const urlParams = new URLSearchParams(imageUrl?.split('?')[1]);
          const imgPath = urlParams.get('path');
          const checkboxId = 'myCheckbox_' + imgPath;
          const checkbox = document.getElementById(checkboxId);
          // Skip if checkbox is checked
          if (checkbox && checkbox.checked) return;
          

          const label = dropdown.querySelector('.dropdown-label');
          const hiddenInput = dropdown.parentElement.querySelector('.selected-category');
          const currentCategory = hiddenInput?.value.trim();

          // Only update if the selected value is different
          if (imageUrl && currentCategory !== selectedValue) {
            imageUrlsToUpdate.push(imageUrl);

            // Update UI immediately
            if (label) label.textContent = selectedValue;
            if (hiddenInput) hiddenInput.value = selectedValue;
          }
        });

        // Only send request if something changed
        if (imageUrlsToUpdate.length > 0) {
          sendBatchCategoryUpdate(jobId, imageUrlsToUpdate, selectedValue);
        }
      });
    });
  }

  // ========================
  // Send Batch Category Update
  // ========================
  function sendBatchCategoryUpdate(jobId, imageUrls, category) {
    fetch('/update-all-categories', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        job_id: jobId,
        image_urls: imageUrls,
        category: category
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success' && data.labeled_data_counts) {
        updateCountsDropdown(data.labeled_data_counts, data.f1_score, data.accuracy_score);
      } else {
        console.error('Server error:', data.message);
      }
    })
    .catch(error => {
      console.error('Error sending batch category update:', error);
    });
  }
    
});














document.addEventListener('DOMContentLoaded', function () {
    const modalImage = document.getElementById('modalImage');
    
    if (!modalImage) {
        console.warn("Warning: 'modalImage' element not found in the document.");
        return; // Exit early to avoid errors
    }
    
    document.querySelectorAll('.popup-image').forEach(img => {
        img.addEventListener('click', function () {
            const src = this.getAttribute('data-img-src');
            if (src) {
                modalImage.setAttribute('src', src);
            } else {
                console.warn("Warning: Image source not found on clicked element.");
            }
        });
    });
});


document.addEventListener("DOMContentLoaded", function () {
    const toggles = document.querySelectorAll('[data-bs-toggle="collapse"]');

    toggles.forEach(toggle => {
        const targetId = toggle.getAttribute("data-bs-target");
        const target = document.querySelector(targetId);
        const arrow = toggle.querySelector(".collapse-toggle");

        if (target) {
            target.addEventListener("show.bs.collapse", () => {
                if (arrow) arrow.textContent = "▲";
            });

            target.addEventListener("hide.bs.collapse", () => {
                if (arrow) arrow.textContent = "▼";
            });
        }
    });
});


function sendCategoryUpdate(jobId, imageUrl, category, operation, source) {
    fetch('/update-category', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        job_id: jobId,
        image_url: imageUrl,
        category: category,
        operation: operation,
        source: source
          
      }),
    })
    .then(response => response.json())
    .then(data => {
        // console.log('Category update response:', data);
        if (data.status === 'success' && data.labeled_data_counts) {
          updateCountsDropdown(data.labeled_data_counts, data.f1_score, data.accuracy_score );
    
        }
    })
    .catch(error => {
      console.error('Error sending category update:', error);
    });
}


function onCheckboxChange(checkbox, jobId, imageUrl, category) {
      if (checkbox.checked) {
        // console.log("Checkbox is checked", jobId, imageUrl, category );
        // Your code for checked state here

          sendCategoryUpdate(jobId, imageUrl, category, "add", "checkbox" );
          
      } else {
        // console.log("Checkbox is unchecked", jobId, imageUrl, category);
        // Your code for unchecked state here

          sendCategoryUpdate(jobId, imageUrl, category, "remove", "checkbox");
      }
    }
