(this["webpackJsonpslowdraft-front-end"]=this["webpackJsonpslowdraft-front-end"]||[]).push([[0],{21:function(e,t,n){e.exports=n(39)},26:function(e,t,n){},32:function(e,t,n){},33:function(e,t,n){},34:function(e,t,n){},39:function(e,t,n){"use strict";n.r(t);var a=n(0),l=n.n(a),r=n(16),c=n.n(r),o=(n(26),n(9)),u=n(19),m=n(2),s=n(4),i=n(17);n(32);function E(){var e=l.a.useMemo((function(){return[{col1:"Hello",col2:"World"},{col1:"react-table",col2:"rocks"},{col1:"whatever",col2:"you want"}]}),[]),t=l.a.useMemo((function(){return[{Header:"Column 1",accessor:"col1"},{Header:"Column 2",accessor:"col2"}]}),[]),n=Object(i.useTable)({columns:t,data:e}),a=n.getTableProps,r=n.getTableBodyProps,c=n.headerGroups,o=n.rows,u=n.prepareRow;return l.a.createElement("table",a(),l.a.createElement("thead",null,c.map((function(e){return l.a.createElement("tr",e.getHeaderGroupProps(),e.headers.map((function(e){return l.a.createElement("th",e.getHeaderProps(),e.render("Header"))})))}))),l.a.createElement("tbody",r(),o.map((function(e){return u(e),l.a.createElement("tr",e.getRowProps(),e.cells.map((function(e){return l.a.createElement("td",e.getCellProps(),e.render("Cell"))})))}))))}var h=n(41);n(33);function d(e){return l.a.createElement("div",{className:"App"},!1===e.loginStatus&&l.a.createElement("div",{className:"login-container"},l.a.createElement("h1",null,"Slow",l.a.createElement("span",null,"Draft")),l.a.createElement("p",null,"Fantasy hockey drafting at your own pace"),l.a.createElement("p",null,"Currently by invitation only"),!1,l.a.createElement("div",{className:"connect-to-yahoo"},l.a.createElement(h.a,{className:"connect-button",onClick:void fetch("/login",{method:"GET"}).then((function(e){return e.json()})).then(e.setLoggedIn)},"Sign in with \xa0",l.a.createElement("img",{alt:"Yahoo",src:"yahoo.png",width:"57",height:"16"})))),!0===e.loginStatus&&l.a.createElement(s.d,{className:"navbar-tabs"},l.a.createElement(s.b,null,l.a.createElement(s.a,null,"1"),l.a.createElement(s.a,null,"2"),l.a.createElement(s.a,null,"3")),l.a.createElement(s.c,null,l.a.createElement("h2",null,"tab 1 content"),l.a.createElement(E,null)),l.a.createElement(s.c,null,l.a.createElement("h2",null,"tab 2 content")),l.a.createElement(s.c,null,l.a.createElement("h2",null,"tab 3 content"))))}function f(){var e=Object(a.useState)(),t=Object(o.a)(e,2),n=t[0],r=t[1];return l.a.createElement(s.d,{className:"navbar-tabs"},l.a.createElement(s.b,null,l.a.createElement(s.a,null,"1"),l.a.createElement(s.a,null,"2"),l.a.createElement(s.a,null,"3")),l.a.createElement(s.c,null,l.a.createElement("h2",null,"tab 1 content"),l.a.createElement("button",{onClick:function(){fetch("/test").then((function(e){return e.json()})).then((function(e){r(e.test)}))}},"test"),"Test: ",n),l.a.createElement(s.c,null,l.a.createElement("h2",null,"tab 2 content")),l.a.createElement(s.c,null,l.a.createElement("h2",null,"tab 3 content")))}n(34),n(35);function b(){var e=Object(a.useState)(!1),t=Object(o.a)(e,2),n=t[0],r=t[1];return l.a.createElement(l.a.Fragment,null,l.a.createElement(u.a,null,l.a.createElement(m.c,null,l.a.createElement(m.a,{exact:!0,path:"/"},l.a.createElement(d,{loginStatus:n,login:r})),l.a.createElement(m.a,{exact:!0,path:"/navbar"},l.a.createElement(f,null),l.a.createElement(E,null)))))}Boolean("localhost"===window.location.hostname||"[::1]"===window.location.hostname||window.location.hostname.match(/^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/));c.a.render(l.a.createElement(l.a.StrictMode,null,l.a.createElement(b,null)),document.getElementById("root")),"serviceWorker"in navigator&&navigator.serviceWorker.ready.then((function(e){e.unregister()})).catch((function(e){console.error(e.message)}))}},[[21,1,2]]]);
//# sourceMappingURL=main.3dc714d3.chunk.js.map