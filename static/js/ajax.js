$(".reg").submit(function(e){
    e.preventDefault();
    var action_url = $(this).attr("action")
    formData = new FormData($(this).get(0));
    $.ajax({
        type: "POST",
        url: action_url,
        data: formData,
        contentType: false,
        processData: false,
        success: function(response){
            if ("success" in response){
                document.querySelector('.form-erros-signup').innerHTML = "<b>All Done</b>"
                location.reload()
            }
            else if("error" in response){
                document.querySelector('.form-erros-signup').innerHTML = "<b>Form errors</b>"
                for (let key in response["error"]) {
                    document.querySelector('.form-erros-signup').innerHTML += key + ": " + response["error"][key] + "</br>"
                }
            }
        }
    })
})
$(".log").submit(function(e){
    e.preventDefault();
    var action_url = $(this).attr("action")
    formData = new FormData($(this).get(0));
    $.ajax({
        type: "POST",
        url: action_url,
        data: formData,
        contentType: false,
        processData: false,
        success: function(response){
            if ("success" in response){
                location.replace("http://127.0.0.1:8000/")
            }
            else if("error" in response){
                document.querySelector('.form-erros-login').innerHTML = "<b>" + response["error"] + "</b>"
            }
        }
    })
})

const form_container = document.querySelector(".navbar")
if (form_container){
form_container.addEventListener("click", function(e) {
	const target = e.target;
	if (target.classList.contains("user_image") || target.classList.contains("no_image")) {
        if (target.classList.contains("user_image") || target.classList.contains("no_image")) {
            form = document.querySelector(".img")
            form.classList.toggle("active")
        }
        all_forms = document.querySelectorAll(".img")
        for (let i = 0; i < all_forms.length; i++) {
            if(form != all_forms[i]){
                all_forms[i].classList.remove("active")
            }    
        }
        actives = false
        for (let i = 0; i < all_forms.length; i++) {
            if(all_forms[i].classList.contains('active')){
                actives = true;
                break;
            }    
        }
        if (actives) {
            document.querySelector('body').classList.add('stop')
        } 
        else{
            document.querySelector('body').classList.remove('stop')
        }
	}
})
}