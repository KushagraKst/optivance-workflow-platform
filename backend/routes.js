module.exports = function(app){

app.get('/tasks',(req,res)=>{
res.json([
{id:1,title:"UI Design",status:"Pending"},
{id:2,title:"API Development",status:"In Progress"}
])
})

}