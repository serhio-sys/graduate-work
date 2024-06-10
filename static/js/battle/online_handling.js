socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.is_connected && enemy === "None") {
        window.location.reload();
    } else if (data.selected != null) {
        switch (data.selected.attack){
            case "head": document.querySelector("#id_attack_0").checked = true; break;
            case "body": document.querySelector("#id_attack_1").checked = true; break;
            case "legs": document.querySelector("#id_attack_2").checked = true; break;
        }
        switch (data.selected.defence){
            case "head": document.querySelector("#id_defence_0").checked = true; break;
            case "body": document.querySelector("#id_defence_1").checked = true; break;
            case "legs": document.querySelector("#id_defence_2").checked = true; break;
        }
        document.querySelector(".attack_submit").classList.add("disabled");
    } else if (data.attack_data) {
        const parsed_data = JSON.parse(data.attack_data);
        if (parsed_data.is_finish === true) {
            window.location.replace(finish_redirect);
        } 
        if (userId !== parsed_data.id) {
            setEffects(parsed_data.user_stats, parsed_data.enemy_stats);
            setHp(parsed_data.user_hp, parsed_data.enemy_hp);
        } else {    
            setEffects(parsed_data.enemy_stats, parsed_data.user_stats);
            setHp(parsed_data.enemy_hp, parsed_data.user_hp);  
        } 
        addLog(parsed_data.log);  
        document.querySelector(".countdown_timer").innerHTML = waiting_both_attack;
        document.querySelector(".attack_submit").classList.remove("disabled");
    } else if (data.time != null && data.time[userId]) {
        document.querySelector(".countdown_timer").innerHTML = attack_countdown + data.time[userId];
    } 
    if (data.logs) {
        addLogs(data.logs);
    }
};

document.querySelector('.attack_form').addEventListener('submit', async (e) => {
    e.preventDefault()
    var attack_data = e.target.elements['attack'].value;
    var defence_data = e.target.elements['defence'].value;
    var data = {
        'attack': attack_data,
        'defence': defence_data
    };

    socket.send(JSON.stringify(data));
    document.querySelector(".countdown_timer").innerHTML = attack_process;
    document.querySelector(".attack_submit").classList.add("disabled");
});

function addLogs(logs) {
    var add_text = ""
    logs.forEach(item => {
        add_text += `<span>${item}</span><br>`
    })
    logs_chat.innerHTML += add_text
    logs_chat.scrollTop = logs_chat.scrollHeight
}