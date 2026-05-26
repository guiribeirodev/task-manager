using Microsoft.EntityFrameworkCore;
using OrganizeMyLife.Data;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddDbContext<AppDbContext>(opt => opt.UseInMemoryDatabase("TodoList"));
builder.Services.AddDatabaseDeveloperPageExceptionFilter();

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddOpenApiDocument(config =>
{
    config.DocumentName = "TodoAPI";
    config.Title = "TodoAPI v1";
    config.Version = "v1";
});

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseOpenApi();
    app.UseSwaggerUi(config =>
    {
        config.DocumentTitle = "TodoAPI";
        config.Path = "/swagger";
        config.DocumentPath = "/swagger/{documentName}/swagger.json";
        config.DocExpansion = "list";
    });
}

RouteGroupBuilder todoItems = app.MapGroup("/todoitems");

todoItems.MapGet("/", GetAllTodos);
todoItems.MapGet("/complete", GetCompleteTodos);
todoItems.MapGet("/{id}", GetTodo);
todoItems.MapPost("/", CreateTodo);
todoItems.MapPut("/{id}", UpdateTodo);
todoItems.MapDelete("/{id}", DeleteTodo);

app.Run();

static async Task<IResult> GetAllTodos(AppDbContext db)
{
    return TypedResults.Ok(await db.Todos.Select(x => new TodoItemDto(x)).ToArrayAsync());
}

static async Task<IResult> GetCompleteTodos(AppDbContext db) {
    return TypedResults.Ok(await db.Todos.Where(t => t.State == TodoState.Done).Select(x => new TodoItemDto(x)).ToListAsync());
}

static async Task<IResult> GetTodo(int id, AppDbContext db)
{
    return await db.Todos.FindAsync(id)
        is OrganizeMyLife.Data.Todo todo
            ? TypedResults.Ok(new TodoItemDto(todo))
            : TypedResults.NotFound();
}

static async Task<IResult> CreateTodo(TodoItemDto todoItemDTO, AppDbContext db)
{
    var todoItem = new OrganizeMyLife.Data.Todo
    {
        Title = todoItemDTO.Title,
        Description = todoItemDTO.Description,
        State = todoItemDTO.State,
        UserId = todoItemDTO.UserId > 0 ? todoItemDTO.UserId : 1 // just a quick fallback to avoid FK constraints errors if they exist
    };

    db.Todos.Add(todoItem);
    await db.SaveChangesAsync();

    todoItemDTO = new TodoItemDto(todoItem);

    return TypedResults.Created($"/todoitems/{todoItem.Id}", todoItemDTO);
}

static async Task<IResult> UpdateTodo(int id, TodoItemDto todoItemDTO, AppDbContext db)
{
    var todo = await db.Todos.FindAsync(id);

    if (todo is null) return TypedResults.NotFound();

    todo.Title = todoItemDTO.Title;
    todo.Description = todoItemDTO.Description;
    todo.State = todoItemDTO.State;
    if(todoItemDTO.UserId > 0)
    {
        todo.UserId = todoItemDTO.UserId;
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