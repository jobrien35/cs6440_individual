/*
 * Proof of concept CREST API queried and cached in browser
*/
var max = 500;
var rateLimit = 0;


/*
 * determine if browser supports localStorage
 * then determine if the data is already cached
 * returns data if cached or null if nothing there
*/
function getCached(queryStr) {
    var data = null;
    if (typeof(Storage) !== "undefined") {
        // if you have stored it before, otherwise already null
        if (localStorage.getItem(queryStr) !== null) {
            data = localStorage.getItem(queryStr);
        }
    }
    else {
        console.log("[!!] localStorage unsupported");
    }
    return data;
}

function cache(key, data) {
    // stringify the object so getItem returns the object
    localStorage.setItem(key, data);
}




function retrievePid() {
    var pid = getCached('pid')
    if (pid === null) {
        pid = "..."
    }
    console.log('retieved pid: ')
    console.log(pid)
    return pid;
}

function storePid(pid) {
    cache('pid', pid);
    console.log('stored pid: ')
    console.log(pid)
}