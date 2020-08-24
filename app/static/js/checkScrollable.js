
if (document.body.scrollHeight > document.body.clientHeight + 32) {
    var jumbotron = document.getElementById("jumbotron");
    jumbotron.classList.remove("vh-md-90");
    var logo = document.getElementById("logo");
    logo.classList.remove("position-absolute");
}
