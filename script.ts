import { prisma } from "./lib/prisma";

async function main() {
    const todo = await prisma.todo.create({
        data: {
            title: "Mercado",
            description: 'Fazer compras',
            completed: false,
        }
    })

    const allTodo = await prisma.todo.findMany()

    console.log(allTodo)
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });