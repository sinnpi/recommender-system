document.addEventListener('DOMContentLoaded', function() {
    // Add event listener to each rating button
    var ratingButtons = document.querySelectorAll('.rating-btn');
    ratingButtons.forEach(function(button) {
        button.addEventListener('click', rateMovie);
    });
    
});

function rateMovie(event) {
    event.preventDefault();

    var movieId = this.getAttribute('data-movieId');
    var rating = this.getAttribute('data-rating');
    var invokingElement = this

    rate_movie_url = appConfig['urls']['rate_movie']
    // jQuery AJAX call
    $.ajax({
        url: rate_movie_url,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            'movie_id': movieId,
            'rating': rating
        }),
        dataType: 'json',
        success: function (data) {
            console.log('Success:', data);
            // Update the rating display
            // change the color of the rating button clicked
            var ratingButtons = invokingElement.parentElement.querySelectorAll('.rating-btn');
            for (var i = 0; i < ratingButtons.length; i++) {
                if (ratingButtons[i].getAttribute('data-rating') == rating) {
                    ratingButtons[i].classList.add('ChosenRating');
                    // ratingButtons[i].classList.remove('btn-primary');

                }
                else {
                    ratingButtons[i].classList.remove('ChosenRating');
                    // ratingButtons[i].classList.add('btn-primary');

                }
            }


        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.error('Error loading data:', textStatus, errorThrown);
            // Handle errors
        }
    });
}