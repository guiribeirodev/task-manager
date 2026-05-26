using Microsoft.EntityFrameworkCore;
using OrganizeMyLife;
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
// todoItems.MapGet("/complete", GetCompleteTodos);
todoItems.MapGet("/{id}", GetTodo);
todoItems.MapPost("/", CreateTodo);
todoItems.MapPut("/{id}", UpdateTodo);
todoItems.MapDelete("/{id}", DeleteTodo);

RouteGroupBuilder users = app.MapGroup("/users");

users.MapGet("/", GetAllUsers);
users.MapPost("/", CreateUser);
users.MapPut("/{id}", UpdateUser);
users.MapDelete("/{id}", DeleteUser);

app.Run();

static async Task<IResult> GetAllUsers(AppDbContext db)
{
    var allUsers = await db.Users.ToArrayAsync();
    return TypedResults.Ok(allUsers);
}

static async Task<IResult> CreateUser(UserDto userDto, AppDbContext db)
{
    var newUser = new OrganizeMyLife.Data.User
    {
        Username = userDto.Username,
        Email = userDto.Email,
        Password = userDto.Password
    };

    await db.Users.AddAsync(newUser);
    await db.SaveChangesAsync();
    
    return TypedResults.Ok(newUser);
}

static async Task<IResult> UpdateUser(int id, UserDto userDto, AppDbContext db)
{
    var user = await db.Users.FindAsync(id);
    
    if (user is null) return TypedResults.NotFound();
    
    user.Username = userDto.Username;
    user.Email = userDto.Email;
    user.Password = userDto.Password;
    await db.SaveChangesAsync();
    
    return TypedResults.NoContent();
}

static async Task<IResult> DeleteUser(int id, AppDbContext db)
{
    var user = await db.Users.FindAsync(id);
    
    if (user is null) return TypedResults.NotFound();
    
    db.Users.Remove(user);
    await db.SaveChangesAsync();
    
    return TypedResults.NoContent();
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