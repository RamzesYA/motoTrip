let text = document.querySelector(".text");
let but = document.querySelector(".but");
text.addEventListener("input", function(){
    if(this.value) {
        but.style.visibility = 'visible';    
    } else {
        but.style.visibility = 'hidden';
    }
});