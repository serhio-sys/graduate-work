function detectMob() {
    const toMatch = [
        /Android/i,
        /webOS/i,
        /iPhone/i,
        /iPad/i,
        /iPod/i,
        /BlackBerry/i,
        /Windows Phone/i
    ];
    
    return toMatch.some((toMatchItem) => {
        return navigator.userAgent.match(toMatchItem);
    });
}

async function lockOrientation() {
    if ("orientation" in screen && detectMob()) {
        try {
            await screen.orientation.lock("landscape-primary");
            console.log("Orientation locked to landscape-primary.");
        } catch (e) {
            showOrientationMessage();
        }
    } else {
        showOrientationMessage();
    }
}

function showOrientationMessage() {
    function checkOrientation() {
        if (window.innerHeight > window.innerWidth) {
            // Portrait
            document.querySelector('.device_message').style.display = 'flex';
            document.querySelector('body').style.background = 'rgba(0, 0, 0, 0.9)';
            document.querySelector('body').style.minWidth = 'auto';
            document.querySelector('.main').style.display = 'none';
        } else {
            // Landscape
            document.querySelector('.device_message').style.display = 'none';
            document.querySelector('body').style.background = 'none';
            document.querySelector('body').style.minWidth = '1200px';
            document.querySelector('.main').style.display = 'block';
        }
    }

    window.addEventListener('resize', checkOrientation);
    window.addEventListener('orientationchange', checkOrientation);

    // Initial check
    checkOrientation();
}

lockOrientation();

document.querySelector('main').style.minHeight = `calc(100vh - ${document.querySelector('.navbar').offsetHeight}px)`;
document.querySelector(".locale")?.addEventListener("change", () => {
    document.querySelector(".locale-form").submit();
})
var lang = "{{request.session.lang}}"
if (lang === "") {
  lang = "uk"
}
document.querySelectorAll("option").forEach(it => {
    if (it.value == lang){
        it.setAttribute("selected", "selected");
    }
})