document.querySelector(".duels").addEventListener("click", async (event) => {
    document.querySelector(".rooms").classList.toggle("hidden");
    await fetchRoomsData();
});

rooms_block.addEventListener("click", event => {
    if (event.currentTarget === rooms_block) {
        rooms_block.classList.add("hidden");
    }
});

connect_password_btn.addEventListener("click", async event => {
    event.cancelBubble = true;
    if (selected !== null) {
        let decoded_pass = decoding(selected.password)
        if (decoded_pass === password_input.value) {
            await connectionProcess();
        }
    }
});

password_input.addEventListener("click", event => {
    event.cancelBubble = true;
});

button_create.addEventListener("click", event => {
    event.cancelBubble = true;
});

button_connect.addEventListener("click", async event => {
    await connectToRoom(event);
});

setInterval(fetchRoomsData, 5000)

function openPasswordInput() {
    document.querySelector(".room_password").classList.remove("hidden")
}

async function fetchRoomsData() {
    if (!rooms_block.classList.contains("hidden")) {
        await fetch(rooms_url, {
            method: "GET",
        }).then(res => {
            return res.json();
        }).then(data => {
            updateRoomList(data);
        });
    }
}

async function connectToRoom(event) {
    event.cancelBubble = true;
    if (selected !== null) {
        if (decoding(selected.password) !== "null") {
            openPasswordInput();
            return;
        }    
        await connectionProcess();
    }
}

async function connectionProcess() {
    if (selected?.id !== undefined) {
        await fetch(rooms_connect_url, {
            method: "POST",
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrftoken},
            body: JSON.stringify({"room_id": selected.id})
        }).then(res => {
            return res.json();
        }).then(data => {
            window.location.replace(data);
        });
    }
}

function encoding(password) {
    let new_password = password
    for (let i = 0; i < 5; i++) {
        new_password = window.btoa(new_password)
    }
    return new_password
}

function decoding(password) {
    let new_password = password
    for (let i = 0; i < 5; i++) {
        new_password = window.atob(new_password)
    }
    return new_password
}

function updateRoomList(data) {
    const rooms_list = document.querySelector(".room_list");
    let innerHTML = "";
    if (data.length == 0) {
        innerHTML += `<div class="text-center">${no_more_rooms_message}</div>`
    } else {
        data.forEach(item => {
            if (item.id === Number.parseInt(selected?.id)) {
                innerHTML += `<div class="d-flex justify-content-between gap-3 p-2 room selected_room" id="${item.id}" password="${encoding(item.password)}"><div>${item.first_player.username}[${item.first_player.lvl}]</div><div>Назва кімнати: ${item.name}</div><div>Взнесок: ${item.rate}</div></div>`;
            } else {
                innerHTML += `<div class="d-flex justify-content-between gap-3 p-2 room" id="${item.id}" password="${encoding(item.password)}"><div>${item.first_player.username}[${item.first_player.lvl}]</div><div>Назва кімнати: ${item.name}</div><div>Взнесок: ${item.rate}</div></div>`;
            }
        })
    }
    rooms_list.innerHTML = innerHTML;
    document.querySelectorAll(".room").forEach(item => settingRoomClickListener(item))
}

function settingRoomClickListener(item) {
    item.addEventListener("click", event => {
        event.cancelBubble = true;
        let id = item.getAttribute("id")
        if (selected?.id === id) {    
            selected = null;
            document.querySelector(".connect-btn").classList.add("disabled")
        } else {
            if (selected !== null) {
                document.getElementById(selected).classList.remove("selected_room")
            }
            selected = {"id": id, "password": item.getAttribute("password")};
            document.querySelector(".connect-btn").classList.remove("disabled")
        }
        event.currentTarget.classList.toggle("selected_room")
    })
}

var elem = document.querySelector(".room_password");
elem.addEventListener("click", () => {
    elem.classList.add("hidden");
});