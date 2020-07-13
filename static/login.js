function login_guest() {
    $.post("/login_as_guest", function() { location.reload(); });
}
