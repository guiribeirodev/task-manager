using Microsoft.EntityFrameworkCore;
using OrganizeMyLife.Data;

namespace OrganizeMyLife.Endpoints;

public static class UserEndpoints
{
    public static void Map(WebApplication app)
    {
        RouteGroupBuilder users = app.MapGroup("/users");

        users.MapGet("/", GetAllUsers);
        users.MapPost("/", CreateUser);
        users.MapPut("/{id}", UpdateUser);
        users.MapDelete("/{id}", DeleteUser);
    }
    
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
}