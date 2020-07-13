function submitPassword() {
    // clear the message div
    $("#message-div").html("");
    // grab the proposed passwords
    var pass1 = $("#password1").val();
    var pass2 = $("#password2").val();

    // verify that they match
    if (pass1 !== pass2) {
        $("#message-div").html("Passwords do not match");
        return;
    }
    // and require length 6 minimum
    if (pass1.length < 6) {
        $("#message-div").html("Password must be at least 6 characters long");
        return;
    }
    // submit if they do
    $.post(
        "/set_password",
        {
            reset_token: resetToken,
            new_pass: pass1
        },
        function (data) {
            console.log(data)
            if (data.success == true) {
                setTimeout(
                    function () { window.location.href = '/login'; },
                    1200
                );
            }
            $("#message-div").html(data.message);
        }
    )
}

$(document).ready(function () {
    $("#submit-password").click(function () {
        submitPassword();
    });
});
