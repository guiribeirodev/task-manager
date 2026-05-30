using Microsoft.EntityFrameworkCore;
using OrganizeMyLife.Data;

namespace OrganizeMyLife.Endpoints;

public static class TodoEndpoints
{
    public static void Map(WebApplication app)
    {
        RouteGroupBuilder todos = app.MapGroup("/todos");

        todos.MapGet("/", GetAllTodos);
        // todos.MapGet("/complete", GetCompleteTodos);
        todos.MapGet("/{id}", GetTodo);
        todos.MapPost("/", CreateTodo);
        todos.MapPut("/{id}", UpdateTodo);
        todos.MapDelete("/{id}", DeleteTodo);
    }
    
    static async Task<IResult> GetAllTodos(AppDbContext db)
    {
        return TypedResults.Ok(await db.Todos.Select(x => new TodoItemDto(x)).ToArrayAsync());
    }

// static async Task<IResult> GetCompleteTodos(AppDbContext db) {
//     return TypedResults.Ok(await db.Todos.Where(t => t.State == TodoState.Done).Select(x => new TodoItemDto(x)).ToListAsync());
// }

    static async Task<IResult> GetTodo(int id, AppDbContext db)
    {
        return await db.Todos.FindAsync(id)
            is OrganizeMyLife.Data.Todo todo
            ? TypedResults.Ok(new TodoItemDto(todo))
            : TypedResults.NotFound();
    }

    static async Task<IResult> CreateTodo(TodoItemDto todoItemDto, AppDbContext db)
    {
        var todoItem = new OrganizeMyLife.Data.Todo
        {
            Title = todoItemDto.Title,
            Description = todoItemDto.Description,
            State = todoItemDto.State,
            UserId = todoItemDto.UserId > 0 ? todoItemDto.UserId : 1 // just a quick fallback to avoid FK constraints errors if they exist
        };

        db.Todos.Add(todoItem);
        await db.SaveChangesAsync();

        todoItemDto = new TodoItemDto(todoItem);

        return TypedResults.Created($"/todoitems/{todoItem.Id}", todoItemDto);
    }

    static async Task<IResult> UpdateTodo(int id, TodoItemDto todoItemDto, AppDbContext db)
    {
        var todo = await db.Todos.FindAsync(id);

        if (todo is null) return TypedResults.NotFound();

        todo.Title = todoItemDto.Title;
        todo.Description = todoItemDto.Description;
        todo.State = todoItemDto.State;
        if(todoItemDto.UserId > 0)
        {
            todo.UserId = todoItemDto.UserId;
        }

        await db.SaveChangesAsync();

        return TypedResults.NoContent();
    }

    static async Task<IResult> DeleteTodo(int id, AppDbContext db)
    {
        if (await db.Todos.FindAsync(id) is OrganizeMyLife.Data.Todo todo)
        {
            db.Todos.Remove(todo);
            await db.SaveChangesAsync();
            return TypedResults.NoContent();
        }

        return TypedResults.NotFound();
    }
}