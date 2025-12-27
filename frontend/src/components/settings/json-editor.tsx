import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"

const mockJson = `{
  "amplis": {
    "username": "user_example",
    "password": "password123",
    "url": "https://amplis.example.com"
  },
  "maps": {
    "api_key": "sk_live_123456"
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "db": "etl_db"
  }
}`

export function JsonEditor() {
    return (
        <div className="grid gap-4">
            <div className="flex items-center justify-between">
                <Label>credentials.json (Preview)</Label>
                <Button variant="outline" size="sm" disabled>Edit (Coming Soon)</Button>
            </div>
            <Textarea
                className="font-mono min-h-[400px]"
                defaultValue={mockJson}
                readOnly
            />
            <p className="text-sm text-muted-foreground">
                Direct editing of credentials is disabled in this version for security. Please edit the file directly on the server.
            </p>
        </div>
    )
}
