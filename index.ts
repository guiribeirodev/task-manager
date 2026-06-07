import express from 'express';
import { prisma } from './lib/prisma';

const app = express();
const port = 3000;

app.use(express.json());

app.post('/todos', async (req, res) => {
  const todo2 = req.body
  console.log(req);
  console.log(todo2)
  const newTodo = await prisma.todo.create({
        data: {
            title: todo2.title,
            description: todo2.description,
            completed: todo2.completed,
        }
    })

  res.json(newTodo);
});

app.get('/', (req, res) => {
  res.send('Hello World!');
});


app.get('/todos', async (req,res) => {
  const allTodos = await prisma.todo.findMany();

  res.json(allTodos)
});


app.get('/todos/:id', async (req, res) => {
  const id = parseInt(req.params.id);

  const todo = await prisma.todo.findUnique(
    {
      where: {id}
    }
  );

  res.json(todo)
});

app.put('/todos/:id', async (req, res) => {
  const id = parseInt(req.params.id);
  const reqBody = req.body;

  let todo =  await prisma.todo.update({
    where: {id},
    data: {
      completed: reqBody.completed,
      title: reqBody.title,
      description: reqBody.description,
      updatedAt: new Date()
    }
  });

  res.json(todo)

});

app.delete('/todos/:id', async (req, res) => {
  const id = parseInt(req.params.id)

  await prisma.todo.delete({
    where: {id}
  })

  res.sendStatus(204)
})


app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`);
});