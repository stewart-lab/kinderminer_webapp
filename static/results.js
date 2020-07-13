function deleteRequest(reqID) {
    // just send a post and refresh
    $.post('/delete_request',
        { request_id: reqID },
        function (data) {
            location.reload();
        }
    );
}

function clickDeleteRequest(reqID, reqName) {
    // attach the actual delete to the modal confirm button
    $('#deleteConfirmButton').attr('onclick', 'deleteRequest(' + reqID + ')');
    // set the modal text
    $('#deleteReqName').text('[ ' + reqName + ' ]');
    // and show the modal
    $('#deleteModal').modal();
}

function downloadResults(reqID) {
    // just send a get and deal with the text response
    $.get('/download_results/' + reqID,
        { fet_cutoff: '1.0' },
	function(data) {
            // need to do some fancy footwork to show the download dialog
            // turn the returned text into a data blob
	    var data = new Blob([data], {type: 'text/csv'});
            // and create a URL for the blob data
	    var url = window.URL.createObjectURL(data);
            // grab the hidden link on the page and attach the URL
	    var link = document.getElementById('download_link');
	    link.href = url;
	    link.download = 'results.csv';
            // and click that hidden link
	    link.click();
            // now get rid of the URL
	    window.URL.revokeObjectURL(url);
	}
    );
}

$(document).ready(function () {
    // put together our print options for dates
    var localeStrOpts = {day: '2-digit', month: '2-digit', year: 'numeric',
                         hour: '2-digit', minute: '2-digit'};
    // convert all of the request times to local
    var dateSpans = $('.convertToLocalTime');
    dateSpans.each(function() {
        // grab the current span for processing and parse the date string
	var currSpan = $(this);
        // we need to explicitly tell this Date that it is in UTC
	var dutc = new Date(currSpan.text() + "+00:00"); // kind of a no-no
        // so that we can print it in the correct locale
	currSpan.text(dutc.toLocaleString('default', localeStrOpts));
    });
});
