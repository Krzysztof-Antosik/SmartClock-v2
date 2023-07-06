import micropydatabase, os

database = micropydatabase.Database.open("database")

t_strings = database.open_table("strings")
t_count = database.open_table("count")
t_settings = database.open_table("settings")
t_time = database.open_table("time")

def addCount():
    last = t_count.find({"all": 1})
    last = last["last"]
    nextID = last + 1
    t_count.update({"last": last, "all": 1}, {"last": nextID, "all": 1})

def readCount():
    last = t_count.find({"all": 1})
    last = last["last"]
    return last

def headerPage():
    return '''
    <html>
        <head>
            <link rel="shortcut icon" href="data:image/x-icon;," type="image/x-icon">
            <title>SmartClock v2</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta charset="utf-8"/>
            <style>body {
                    margin: 0;
                    font-family: Arial, Helvetica, sans-serif;
                }
                h1, p, form {
                    margin: 0;
                }
                header {
                    position: sticky;
                    top: -54px;
                    text-align: center;
                }
                nav {
                    overflow: hidden;
                    background-color: #333;
                    display: flex;
                    justify-content: flex-start;
                    flex-wrap: wrap;
                }

                nav a {
                    float: left;
                    color: #f2f2f2; 
                    text-align: center;
                    padding: 14px 16px;
                    text-decoration: none;
                    font-size: 17px;
                }

                nav a:hover {
                    background-color: #ddd;
                    color: black;
                }

                nav a.active {
                    background-color: #04AA6D;
                    color: white;
                }
                input {
                    width: 100%;
                    height: 50px;
                }
                table {
                    caption-side: bottom;
                    border-collapse: collapse;
                    border-bottom: 1px solid black;
                    margin-bottom: 20px;
                }
                tbody, tr, td, th {
                    border-color: inherit;
                    border-style: solid;
                    border-width: 0;
                    min-height: 50px;
                }
                td:first-child {
                    width: 100%;
                    word-break: break-word;
                }
                button {
                    font-weight: 600;
                    color: #55595c;
                    cursor: pointer;
                    border: 0 solid black;
                    padding: 0.75rem 1.5rem;
                    font-size: 1rem;
                }
                main {
                    margin: 10px
                }
                a {
                    display: inline-block;
                }
            </style>
        </head>
        <body>
            <header>
                <h1>SmartClock v2</h1>
                <p>by Krzysztof Antosik</p>
                <nav>
                    <a href="/">Home</a>
                    <a href="/alarms">Alarms</a>
                    <a href="/settings">Settings</a>      
                    <a href="/about">About</a>
                </nav>
            </header>'''

def footerPage(page = "/"):
    return '''<script>
                document.querySelector(`a[href="{}"]`).classList.add(`active`);
            </script>
        </html>'''.format(page)

def homePageStart():       
    return '''<main>
                <table>
                    <tbody>
                        <tr>
                        <th colspan="2">
                            <h2>Strings</h2>
                        </th>
                            <th colspan="1">
                                <a href="/add">
                                    <button>Add new</button>
                                </a>
                            </th>
                        </tr>'''
            
def homePageEnd():
    return '''</tbody>
            </table>
        </main>'''

def addPage():
    return '''<main>
                <form action="/added" method="post" accept-charset="utf-8" enctype="text/plain">
                    <input type="text" name="newText"/>
                    <button type="submit">Save</button>
                </form>
                <a href="/"><button>Cancel</button></a>
            </main>
            '''

def addedPage(newText):
    addCount()
    lastID = readCount()
    t_strings.insert({"string": newText, "id": lastID, "all": 1})
    return '''<main>
                <h2>Added</h2>
                <a href="/">
                    <button>ok</button>
                </a>
            </main>
        </body>'''

def editPage(idText = ""):
    string = t_strings.find({"id": int(idText)})

    return '''<main>
                <form action="/update" method="post" accept-charset="utf-8" enctype="text/plain">
                    <input type="hidden" value="{}" name="id">
                    <input type="text" value="{}" name="newText">
                    <button type="submit">save</button>
                </form>
                <a href="/">
                    <button type="cancel">cancel</button>
                </a>
            </main>
            </body>'''.format(string["id"], string["string"])

def updatePage(idText="", newText=""):
    string = t_strings.find({"id": int(idText)})
    t_strings.update(string, {"string" : newText, "id" : string["id"], "all" : 1})
    return '''<main>
                <h2>Updated</h2>
                <a href="/">
                    <button>ok</button>
                </a>
            </main>
            </body>'''

def removePage(idText):
    
    t_strings.delete({"id": int(idText)})
    return '''<main>
                <h2>Removed</h2>
                <a href="/">
                    <button>ok</button>
                </a>
            </main>
        </body>'''

def passwordPage(ssid, secure):
    if int(secure) > 0:
        inputPassowrd = '<input type="password" placeholder="password" name="password">'
    else:
        inputPassowrd = '<p>This connection is unencrypted. Are you sure to half connect?</p>'
    return '''<main>
                <h2>{}</h2>
                <form action="/connect" method="post" accept-charset="utf-8" enctype="text/plain">
                    <input type="hidden" value="{}" name="ssid">
                    {}
                    <button type="submit">connect</button>
                </form>
                <a href="/settings">
                    <button type="cancel">cancel</button>
                </a>
            </main>'''.format(ssid, ssid, inputPassowrd)

def connectPage(success):
    if success:
        return '''<main>
                    <h2>connected</h2>
                    <a href="/settings">
                        <button>ok</button>
                    </a>
                </main>
            </body>'''
    else:
        return '''<main>
                    <h2>Failed</h2>
                    <a href="/settings">
                        <button>ok</button>
                    </a>
                </main>
            </body>'''

def aboutPage():
    settings = t_settings.find({"all": 1})
    return '''<main>
                <h2>SmartClock v2</h2>
                <p>Created by Krzysztof Antosik</p>
                <p>Softwere version: {}</p>
                <p>More projects can be found on the website: <a href="https://antosik.dev">Antosik.dev</a></p>
            </main>'''.format(settings["version"])

def displayOffPage():
    return '''<main>
                <h2>Turned off</h2>
                <a href="/settings">
                    <button>ok</button>
                </a>
            </main>'''

def displayOnPage():
    return '''<main>
                <h2>Turned on</h2>
                <a href="/settings">
                    <button>ok</button>
                </a>
            </main>'''

def timezoneSwitchPage():
    return '''<main>
                <h2>Timezone has turned</h2>
                <a href="/settings">
                    <button>ok</button>
                </a>
            </main>'''
