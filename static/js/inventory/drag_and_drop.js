document.querySelectorAll('.sell_form').forEach(item => {
        
    item.addEventListener('submit', async (e) => {
        e.preventDefault();
        let sellSumAttribute = e.target.querySelector('.btn').getAttribute('data-sell-sum');
        await fetch(item.action, {
            method: "POST",
            headers: {'X-CSRFToken': csrftoken} 
        }).then(res => {
            if (res.status == 200) {
                user_balance += parseInt(sellSumAttribute)
                balance.innerHTML = `{% trans "Рахунок: " %}${user_balance}  $`
                item.parentElement.parentElement.remove();
            }
        });
    });
});

function allowDrop(ev) {
    ev.preventDefault();
}

function dragEq(ev, item, pk) {
    ev.dataTransfer.setData('type', item);
    ev.dataTransfer.setData('pk', pk);
}
  
async function dropEq(ev) {
    ev.preventDefault();
    var dataString = ev.dataTransfer.getData('type');
    var ds = ev.dataTransfer.getData('pk')
    if (dataString === "armor"){
        await fetch(Url+"game/equip_armor/", {
            method: "POST",
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrftoken},
            body: JSON.stringify({"pk": ds}) 
        }).then(res => {
        console.log("Request complete! response:", res);
        });
    } else if (dataString === "weapon"){
        await fetch(Url+"game/equip_weapon/", {
            method: "POST",
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrftoken}, 
            body: JSON.stringify({"pk": ds})
        }).then(res => {
        console.log("Request complete! response:", res);
        });
    } 
    window.location.reload()
}

function dragDeq(ev, deq_type, item) {
    ev.dataTransfer.setData('type', item);
    ev.dataTransfer.setData('deq', deq_type)
}
  
async function dropDeq(ev) {
    var dataString = ev.dataTransfer.getData('type');
    var deq = ev.dataTransfer.getData('deq');
    ev.preventDefault();
    if (dataString === "armor"){
        await fetch(Url+"game/equip_armor/", {
            method: "POST",
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrftoken},
            body: JSON.stringify({"dequip": true}) 
        }).then(res => {
        console.log("Request complete! response:", res);
        });
    } else if (dataString === "weapon"){
        await fetch(Url+"game/equip_weapon/", {
            method: "POST",
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrftoken}, 
            body: JSON.stringify({"dequip": deq})
        }).then(res => {
        console.log("Request complete! response:", res);
        });
    }
    window.location.reload()
}