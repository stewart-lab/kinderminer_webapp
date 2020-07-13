function downloadResults(reqID, fetCutoff) {
    // send a get and deal with the text response
    $.get('/download_results/' + reqID,
        { fet_cutoff: fetCutoff },
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

function updateTableForCutoff(tableRowValTups, value) {
    // we changed our p-value cutoff, so we need to hide and show table rows
    // we already pre-loaded our rows with their values, just iterate
    let meetThreshCount = 0;
    for (i = 0; i < tableRowValTups.length; i++) {
        // meets cutoff
        if (tableRowValTups[i].val <= value) {
            $(tableRowValTups[i].row).show();
            meetThreshCount++;
        }
        // does not meet cutoff
        else {
            $(tableRowValTups[i].row).hide();
        }
    }
    $('#meet_thresh').html(meetThreshCount);
}

function updateChartForCutoff(pValueChart, pCutoffLine, value) {
    // find the rank of the new value in the p-values and update the chart
    var ind = 1;
    while (ind < pVals.length && pVals[ind] <= value) {
        ind++;
    }
    ind--; // back off the rank one to put it back to the <= rank
    // update the cutoff line
    pCutoffLine.data[0].x = ind; // the bottom point
    pCutoffLine.data[1].x = ind; // the top point
    // and redraw the chart with no animation
    pValueChart.update(0);
}

function updateSliderValBoxForCutoff(sliderValBox, value) {
    // we just want to change what's displayed in the box showing the cutoff
    sliderValBox.val(value);
}

function updateSliderForCutoff(slider, value) {
    // we want to change what the slider is set to
    slider.val(value);
}

// these two need to (un)scale symmetrically to make a log-scale like slider
function scaleVal(value) {
    return Math.pow(value, 4.0);
}
function unscaleVal(value) {
    return Math.pow(value, 0.25);
}

$(document).ready(function () {
    // sanity check
    console.log("hit document ready function");

    // initialize the vertical cutoff line on the p-value slider
    var pCutoffLine =
    {
        borderColor: "#cd2026",
        pointRadius: 0,
        showLine: true,
        data: [{ x: 0, y: 0.0 }, { x: 0, y: 1.0 }]
    };

    // initialize the p-value elbow curve to display (TODO: optimize?)
    var pValueData = [];
    for (i = 0; i < pVals.length; i++) {
        pValueData.push({ x: i, y: pVals[i] });
    }
    var pValueLine =
    {
        borderColor: "#3e95cd",
        pointRadius: 0,
        showLine: true,
        data: pValueData
    };

    // create the chart
    var ctx = "p_value_chart";
    var pValueChart = new Chart(ctx,
        {
            type: "scatter",
            data: {
                datasets: [pCutoffLine, pValueLine]
            },
            options: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: "Term Filter Threshold"
                },
                scales: {
                    xAxes: [{
                        type: "linear",
                        position: "bottom",
                        ticks: {
                            min: 0,
                            max: pVals.length - 1,
                            display: false
                        },
                        gridLines: {
                            display: false
                        }/*,
                        scaleLabel: {
                            display: true,
                            labelString: "Filter Threshold"
                        }*/
                    }],
                    yAxes: [{
                        scaleLabel: {
                            display: true,
                            labelString: "p-value"
                        }
                    }]
                },
                tooltips: {
                    enabled: false
                },
                responsive: false
            }
        });

    // pre-query all the table rows and associate them with their p-values
    var tableRowValTups = [];
    var pValCells = $(".p_val_cell") // the p-value cells are marked by class
    for (i = 0; i < pValCells.length; i++) {
        var pVal = parseFloat(pValCells[i].innerHTML);
        var tRow = pValCells[i].parentNode;
        tableRowValTups.push({ row: tRow, val: pVal });
    }

    // pre-query the slider and slider val box to display cutoff values
    var slider = $("#p_value_slider");
    var sliderValBox = $("#slider_val_box");
    // attach callbacks to the slider control
    slider.on("input", function (e) {
        // update the chart every whenever the slider slides (slider is scaled)
        let value = scaleVal(parseFloat($(e.target).val())).toPrecision(4);
        updateChartForCutoff(pValueChart, pCutoffLine, value);
        updateSliderValBoxForCutoff(sliderValBox, value);
    });
    slider.on("change", function (e) {
        // update the actual table only once the user has let go (slider is scaled)
        let value = scaleVal(parseFloat($(e.target).val())).toPrecision(4);
        updateTableForCutoff(tableRowValTups, value);
    });
    // and attach callbacks to the slider val box
    sliderValBox.on("input", function (e) {
        // update the slider, figure, and table (slider box is not scaled)
        let value = parseFloat($(e.target).val());
        updateChartForCutoff(pValueChart, pCutoffLine, value);
        updateTableForCutoff(tableRowValTups, value);
        // unscale the value to put the slider in the correct position
        updateSliderForCutoff(slider, unscaleVal(value));
    });

    // set the slider to KM default and trigger the associated events
    sliderValBox.val(0.00001);
    sliderValBox.trigger("input");

    // attach functions to the download buttons
    // download all doesn't use a cutoff
    $("#btn_download_all").on("click", function (e) {
        downloadResults(requestID, 1.0);
    });
    // download filtered uses the current specified cutoff
    $("#btn_download_filtered").on("click", function (e) {
        var fetCutoff = sliderValBox.val();
        downloadResults(requestID, fetCutoff);
    });

});
