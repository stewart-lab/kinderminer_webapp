function clearForm() {
    $("#queryname").val("");
    $("#keyphrase").val("");
    $("#targetterms").val("");
    $("#sepkpbox").prop("checked", false);
}

function clearTerms() {
    $("#targetterms").val("");
}

function addRequest() {
    console.log("hit addRequest");
    var queryName = $("#queryname").val();
    var keyPhrase = $("#keyphrase").val();
    var targetTerms = $("#targetterms").val();
    var censorYear = $("#censoryear").val();
    var sepKP = $("#sepkpbox").prop("checked");
    $.post(
        "/add_request",
        {
            query_name: queryName,
            key_phrase: keyPhrase,
            target_terms: targetTerms,
            sep_kp: sepKP,
            censor_year: censorYear
        },
        function (data) {
            console.log("hit addRequest - response received");
            console.log(data);
            var respSpan = $("#submitresponse");
            if (data.success == true) {
                clearForm();
                var linkText = "My Results".link("/results");
                data.message = "Job Submitted. See your " + linkText + " page.";
                data.message += " You will receive an email upon completion.";
                setTimeout(function () { respSpan.fadeOut(1000); }, 5000);
            }
            respSpan.html(data.message);
            respSpan.show();
        }
    )
}

function fillTargetTermsWithStatic(filename) {
    console.log("hit fillTargetTermsWithStatic")
    $.get(
        "/../static/" + filename,
        function (data) {
            $("#targetterms").val(data);
        }
    );
}

$(document).ready(function () {
    $("#submitquery").click(function () {
        addRequest();
    });

    $("#fillgenes").click(function () {
        fillTargetTermsWithStatic("all_genes.txt");
    });

    $("#filltfs").click(function () {
        fillTargetTermsWithStatic("all_tfs.txt");
    });

    $("#fillligands").click(function () {
        fillTargetTermsWithStatic("all_ligands.txt");
    });

    $("#fillmirnas").click(function () {
        fillTargetTermsWithStatic("all_mirnas.txt");
    });

    $("#filldrugs").click(function () {
        fillTargetTermsWithStatic("all_charlesdrugs.txt");
    });

    // activate the popup hints
    $('[data-toggle="popover"]').popover();
});
