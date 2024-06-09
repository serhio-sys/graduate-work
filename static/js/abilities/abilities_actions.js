function increaseValue(event) {
    var elem = event.target.parentElement;
    var input = document.querySelector('.'+elem.querySelector('input').classList[0]);
    var upgrade_points_elem = document.getElementById('id_upgrade_points')
    var value = parseInt(input.value, 10);
    value = isNaN(value) ? 1 : value;
    if (current_points > 0){    
        value++;
        current_points--;
        upgrade_points_elem.value--;
        document.querySelector('h3').innerHTML = text+current_points;
    }
    input.value = value;
    console.log(input.value)
  }

function decreaseValue(event) {
    var elem = event.target.parentElement;
    var input = document.querySelector('.'+elem.querySelector('input').classList[0]);
    var upgrade_points_elem = document.getElementById('id_upgrade_points')
    var value = parseInt(input.value, 10);
    if (current_points < max_points){
        value = isNaN(value) ? 1 : value;
        if (value > 1){
            value--;
            current_points++;
            upgrade_points_elem.value++;
            document.querySelector('h3').innerHTML = text+current_points;
        }
        else {
            value = 1
        }
    }
    input.value = value;
}