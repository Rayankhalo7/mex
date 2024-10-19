restaurants.forEach(restaurant => {
    const item = document.createElement('div');
    item.classList.add('restaurant-item');
    
    item.innerHTML = `
        <img src="${restaurant.image}" alt="${restaurant.name}" class="restaurant-img">
        <div class="restaurant-details">
            <h2>${restaurant.name}</h2>
            <p class="category">${restaurant.category}</p>
            <div class="rating">
                <span class="star">&#9733;</span>
                <span>${restaurant.rating}</span>
                <span>${restaurant.reviews}</span>
            </div>
            <div class="extra">
                <span class="icon">&#128337;</span>
                <span>${restaurant.deliveryTime}</span>
                <span class="icon">&#128176;</span>
                <span>${restaurant.deliveryCost}</span>
                <span class="icon">&#128717;</span>
                <span>Min. ${restaurant.minOrder}</span>
            </div>
        </div>
        <div class="restaurant-action">
            <button>Jetzt bestellen</button>
        </div>
    `;

    function filterRestaurants() {
            const nameValue = searchName.value.toLowerCase();
            const categoryValue = filterCategory.value;
            const ratingValue = parseFloat(filterRating.value);

            const filteredRestaurants = restaurants.filter(restaurant => {
                const matchesName = restaurant.name.toLowerCase().includes(nameValue);
                const matchesCategory = categoryValue === "" || restaurant.category === categoryValue;
                const matchesRating = isNaN(ratingValue) || restaurant.rating >= ratingValue;
                return matchesName && matchesCategory && matchesRating;
            });

            displayRestaurants(filteredRestaurants);
        }

        applyFilters.addEventListener('click', filterRestaurants);

        // Initial anzeigen
        displayRestaurants(restaurants);

    restaurantList.appendChild(item);



});





