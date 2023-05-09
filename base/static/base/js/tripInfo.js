function showListbox() {
    if (document.getElementById("checkbox").checked) {
        document.getElementById("second_listbox").style.display = "block";
    } else {
        document.getElementById("second_listbox").style.display = "none";
    }
}