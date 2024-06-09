document.querySelector('.attack_form').addEventListener('submit', async (e) => {
    e.preventDefault()
    var attack_data = e.target.elements['attack'].value
    var defence_data = e.target.elements['defence'].value
    var formData = new FormData();

    formData.append('attack', attack_data);
    formData.append('defence', defence_data);
    await fetch(window.location.pathname, {
        method: "POST",
        headers: {'X-CSRFToken': csrftoken}, 
        body: formData
    }).then(res => res.json())
    .then(data => {
        if (data.winner === false){
            window.location.replace(data.redirect_url)
        }
        else if (data.winner === true){
            window.location.replace(data.redirect_url)
        }
        setEffects(data.enemy_stats, data.user_stats)
        setHp(data.user_hp, data.enemy_hp)
        addLog(data.log)
    });
})